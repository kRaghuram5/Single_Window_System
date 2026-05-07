"""
Dispatch & Retry Engine
───────────────────────
Takes a canonical event, translates it, and pushes it to each target
system.  On failure the request is enqueued for exponential-backoff
retry.  Guarantees at-least-once delivery together with the
idempotency engine.
"""

import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import (
    SWSRecord, FactoryRecord, ShopRecord,
    AuditLog, RetryQueueItem,
)
from . import schema_translator as st
from . import ubid_resolver as resolver
from . import idempotency
from . import conflict_detector

log = logging.getLogger("ubid_sync.dispatcher")

# ── Model + UBID-key lookup per system ───────────────────────────────

_MODEL = {
    "SWS":     SWSRecord,
    "FACTORY": FactoryRecord,
    "SHOP":    ShopRecord,
}

_UBID_COL = {
    "SWS":     "ubid",
    "FACTORY": "business_id",
    "SHOP":    "shop_ubid",
}


def _write_to_system(target: str, ubid: str, translated: dict, db: Session) -> dict:
    """Low-level write into a mock system table.  Returns changed fields."""
    model = _MODEL[target]
    col = _UBID_COL[target]
    record = db.query(model).filter(getattr(model, col) == ubid).first()
    if not record:
        raise ValueError(f"{ubid} not found in {target}")

    changed = {}
    for field, value in translated.items():
        if field == col:
            continue  # skip the UBID key itself
        old = getattr(record, field, None)
        if old != value:
            setattr(record, field, value)
            changed[field] = {"old": old, "new": value}

    record.change_source = "MIDDLEWARE"
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    return changed


def dispatch_event(event: dict, db: Session):
    """Process a single canonical event end-to-end.

    event = {
        "request_id": str,
        "ubid": str,
        "source_system": str,       # e.g. "SWS"
        "event_time": datetime,
        "changes": { canonical_field: new_value, ... }
    }
    """
    req_id = event["request_id"]
    ubid = event["ubid"]
    source = event["source_system"]
    event_time = event["event_time"]
    changes = event["changes"]

    # 1. Idempotency check
    if idempotency.is_duplicate(req_id, db):
        log.info("Duplicate request %s — skipping", req_id)
        return

    # 2. Determine targets
    targets = resolver.get_target_systems(ubid, source, db)
    if not targets:
        log.warning("No propagation targets for UBID %s from %s", ubid, source)
        return

    # 3. For each changed field, check conflicts
    filtered_changes = {}
    for field, value in changes.items():
        conflict = conflict_detector.check_and_resolve(
            ubid, field, value, source, event_time, db
        )
        if conflict:
            log.info("Conflict detected for %s.%s — winner: %s",
                     ubid, field, conflict["winning_source"])
            if conflict["should_propagate"]:
                filtered_changes[field] = conflict["resolved_value"]
        else:
            filtered_changes[field] = value

    if not filtered_changes:
        idempotency.mark_processed(req_id, ubid, source, db)
        return

    # 4. Dispatch to each target
    for target in targets:
        # Build canonical payload with only the UBID + changed fields
        canonical_payload = {"ubid": ubid, **filtered_changes}
        translated = st.from_canonical(target, canonical_payload)

        try:
            old_record = _get_current_values(target, ubid, list(translated.keys()), db)
            _write_to_system(target, ubid, translated, db)

            # Audit success
            for can_field, new_val in filtered_changes.items():
                target_field = st.translate_field(source, target, _source_field(source, can_field))
                old_val = old_record.get(st.from_canonical(target, {can_field: ""}).get(can_field, can_field), "")
                db.add(AuditLog(
                    request_id=req_id,
                    ubid=ubid,
                    source_system=source,
                    target_system=target,
                    field_changed=can_field,
                    old_value=str(old_val) if old_val else "",
                    new_value=str(new_val),
                    status="SUCCESS",
                    conflict_flag="RESOLVED" if can_field in changes and can_field not in filtered_changes else "NONE",
                ))
            db.commit()
            log.info("Dispatched %s → %s for %s", source, target, ubid)

        except Exception as exc:
            log.error("Dispatch to %s failed: %s", target, exc)
            _enqueue_retry(req_id, ubid, source, target, canonical_payload, str(exc), db)
            # Audit failure
            db.add(AuditLog(
                request_id=req_id,
                ubid=ubid,
                source_system=source,
                target_system=target,
                field_changed=",".join(filtered_changes.keys()),
                new_value=json.dumps(filtered_changes),
                status="FAILED",
            ))
            db.commit()

    # 5. Mark processed
    idempotency.mark_processed(req_id, ubid, source, db)


def _source_field(system: str, canonical_field: str) -> str:
    """Get the source system's native field name for a canonical field."""
    mapping = st._FROM_CANONICAL.get(system, {})
    return mapping.get(canonical_field, canonical_field)


def _get_current_values(system: str, ubid: str, fields: list, db: Session) -> dict:
    model = _MODEL[system]
    col = _UBID_COL[system]
    record = db.query(model).filter(getattr(model, col) == ubid).first()
    if not record:
        return {}
    return {f: getattr(record, f, None) for f in fields}


# ── Retry logic ──────────────────────────────────────────────────────

def _enqueue_retry(req_id, ubid, source, target, payload, error, db: Session):
    item = RetryQueueItem(
        request_id=f"{req_id}__retry__{target}",
        ubid=ubid,
        source_system=source,
        target_system=target,
        payload=json.dumps(payload),
        error_message=error,
        retry_count=0,
        next_retry_at=datetime.now(timezone.utc) + timedelta(seconds=5),
    )
    db.add(item)
    db.commit()
    log.info("Enqueued retry for %s → %s", source, target)


def process_retry_queue():
    """Called periodically to retry failed dispatches (exponential backoff)."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending = (
            db.query(RetryQueueItem)
            .filter(
                RetryQueueItem.status == "PENDING",
                RetryQueueItem.next_retry_at <= now,
            )
            .all()
        )

        for item in pending:
            payload = json.loads(item.payload)
            ubid = item.ubid
            target = item.target_system
            translated = st.from_canonical(target, payload)

            try:
                _write_to_system(target, ubid, translated, db)
                item.status = "SUCCESS"
                item.retry_count += 1
                item.updated_at = now

                # Audit the successful retry
                db.add(AuditLog(
                    request_id=item.request_id,
                    ubid=ubid,
                    source_system=item.source_system,
                    target_system=target,
                    field_changed="retry_success",
                    new_value=json.dumps(payload),
                    status="SUCCESS",
                    retry_count=item.retry_count,
                ))
                db.commit()
                log.info("Retry succeeded: %s → %s (attempt %d)",
                         item.source_system, target, item.retry_count)

            except Exception as exc:
                item.retry_count += 1
                item.error_message = str(exc)
                if item.retry_count >= item.max_retries:
                    item.status = "EXHAUSTED"
                    log.error("Retry exhausted for %s → %s", item.source_system, target)
                else:
                    backoff = min(2 ** item.retry_count * 5, 60)
                    item.next_retry_at = now + timedelta(seconds=backoff)
                    log.warning("Retry %d failed for %s → %s, next in %ds",
                                item.retry_count, item.source_system, target, backoff)

                db.add(AuditLog(
                    request_id=item.request_id,
                    ubid=ubid,
                    source_system=item.source_system,
                    target_system=target,
                    field_changed="retry_attempt",
                    new_value=str(exc),
                    status="RETRYING" if item.status == "PENDING" else "EXHAUSTED",
                    retry_count=item.retry_count,
                ))
                item.updated_at = now
                db.commit()
    finally:
        db.close()

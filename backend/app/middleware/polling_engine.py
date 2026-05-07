"""
Polling & Listener Engine
─────────────────────────
Periodically polls each mock system for DIRECT changes and feeds
detected updates into the dispatch pipeline.  Uses timestamp-based
incremental polling to avoid re-processing old records.
"""

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import (
    SWSRecord, FactoryRecord, ShopRecord, SyncState,
)
from . import schema_translator as st
from . import dispatcher

log = logging.getLogger("ubid_sync.poller")

# Snapshot of last-seen values per system+ubid to detect real changes
_last_snapshot: dict[str, dict[str, dict]] = {
    "SWS": {},
    "FACTORY": {},
    "SHOP": {},
}

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

# Fields to watch per system (excluding UBID key and metadata)
_WATCH_FIELDS = {
    "SWS":     ["business_name", "registered_address", "authorized_signatory", "contact_email", "status"],
    "FACTORY": ["establishment_name", "factory_addr", "signatory_name", "license_status"],
    "SHOP":    ["shop_name", "shop_location", "owner_name"],
}


def _build_snapshot(system: str, record) -> dict:
    return {f: getattr(record, f, None) for f in _WATCH_FIELDS[system]}


def poll_system(system: str):
    """Poll one system for DIRECT changes and dispatch canonical events."""
    db: Session = SessionLocal()
    try:
        model = _MODEL[system]
        col = _UBID_COL[system]

        # Get all DIRECT records
        records = db.query(model).filter(model.change_source == "DIRECT").all()

        # Update sync state
        sync = db.query(SyncState).filter(SyncState.system_name == system).first()
        if not sync:
            sync = SyncState(system_name=system)
            db.add(sync)

        sync.last_poll_at = datetime.now(timezone.utc)
        sync.poll_count = (sync.poll_count or 0) + 1
        sync.is_healthy = "true"
        db.commit()

        for record in records:
            ubid = getattr(record, col)
            current = _build_snapshot(system, record)
            previous = _last_snapshot[system].get(ubid, {})

            # Find fields that actually changed
            changed_fields = {}
            for field, val in current.items():
                if previous.get(field) != val and val is not None:
                    changed_fields[field] = val

            if not changed_fields:
                # If no fields changed but source is DIRECT, we still need to clear the flag
                # to prevent re-processing the same record every 5 seconds.
                record.change_source = "PROCESSED"
                db.commit()
                continue

            # Convert to canonical field names
            canonical_changes = {}
            for native_field, value in changed_fields.items():
                can_field = st._TO_CANONICAL[system].get(native_field)
                if can_field and can_field != "ubid":
                    canonical_changes[can_field] = value

            if not canonical_changes:
                record.change_source = "PROCESSED"
                db.commit()
                continue

            # Build canonical event
            event = {
                "request_id": f"POLL-{system}-{ubid}-{uuid.uuid4().hex[:8]}",
                "ubid": ubid,
                "source_system": system,
                "event_time": record.updated_at or datetime.now(timezone.utc),
                "changes": canonical_changes,
            }

            log.info("Change detected in %s for %s: %s", system, ubid, canonical_changes)
            dispatcher.dispatch_event(event, db)

            # Update snapshot and reset change_source so we don't re-process
            _last_snapshot[system][ubid] = current
            record.change_source = "PROCESSED"
            db.commit()

    except Exception as exc:
        log.error("Polling %s failed: %s", system, exc)
        try:
            sync = db.query(SyncState).filter(SyncState.system_name == system).first()
            if sync:
                sync.is_healthy = "false"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def poll_all():
    """Poll all registered systems — called by APScheduler every 5 seconds."""
    # Debug log to verify execution
    with open("poller_debug.log", "a") as f:
        f.write(f"Poller executed at {datetime.now()}\n")

    for system in ("SWS", "FACTORY", "SHOP"):
        poll_system(system)

    # Also process retry queue
    dispatcher.process_retry_queue()


def initialize_snapshots():
    """Load current state of all systems into the snapshot cache on startup."""
    db = SessionLocal()
    try:
        for system in ("SWS", "FACTORY", "SHOP"):
            model = _MODEL[system]
            col = _UBID_COL[system]
            for record in db.query(model).all():
                ubid = getattr(record, col)
                _last_snapshot[system][ubid] = _build_snapshot(system, record)
        log.info("Snapshots initialized: SWS=%d, FACTORY=%d, SHOP=%d",
                 len(_last_snapshot["SWS"]),
                 len(_last_snapshot["FACTORY"]),
                 len(_last_snapshot["SHOP"]))
    finally:
        db.close()

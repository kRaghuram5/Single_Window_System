"""
Dashboard API — serves the React frontend.
Provides read endpoints for monitoring + demo-trigger endpoints
for the four demonstration flows.
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    SWSRecord, FactoryRecord, ShopRecord,
    UBIDRegistry, AuditLog, RetryQueueItem, Conflict,
    ProcessedRequest, SyncState,
)
from ..middleware import dispatcher, schema_translator as st, conflict_detector

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ── Read endpoints ───────────────────────────────────────────────────

@router.get("/businesses")
def list_businesses(db: Session = Depends(get_db)):
    """Unified view — shows each UBID's data across all systems."""
    registries = db.query(UBIDRegistry).all()
    result = []
    for reg in registries:
        entry = {"ubid": reg.ubid, "systems": {}}

        sws = db.query(SWSRecord).filter(SWSRecord.ubid == reg.ubid).first()
        if sws:
            entry["systems"]["SWS"] = {
                "business_name": sws.business_name,
                "registered_address": sws.registered_address,
                "authorized_signatory": sws.authorized_signatory,
                "contact_email": sws.contact_email,
                "status": sws.status,
                "updated_at": sws.updated_at.isoformat() if sws.updated_at else None,
            }

        fac = db.query(FactoryRecord).filter(FactoryRecord.business_id == reg.ubid).first()
        if fac:
            entry["systems"]["FACTORY"] = {
                "establishment_name": fac.establishment_name,
                "factory_addr": fac.factory_addr,
                "signatory_name": fac.signatory_name,
                "license_status": fac.license_status,
                "updated_at": fac.updated_at.isoformat() if fac.updated_at else None,
            }

        shop = db.query(ShopRecord).filter(ShopRecord.shop_ubid == reg.ubid).first()
        if shop:
            entry["systems"]["SHOP"] = {
                "shop_name": shop.shop_name,
                "shop_location": shop.shop_location,
                "owner_name": shop.owner_name,
                "updated_at": shop.updated_at.isoformat() if shop.updated_at else None,
            }

        result.append(entry)
    return result


@router.get("/audit-logs")
def list_audit_logs(ubid: str = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if ubid:
        query = query.filter(AuditLog.ubid == ubid)
    return [
        {
            "id": a.id,
            "request_id": a.request_id,
            "ubid": a.ubid,
            "source_system": a.source_system,
            "target_system": a.target_system,
            "field_changed": a.field_changed,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "status": a.status,
            "retry_count": a.retry_count,
            "conflict_flag": a.conflict_flag,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
        }
        for a in query.limit(limit).all()
    ]


@router.get("/conflicts")
def list_conflicts(db: Session = Depends(get_db)):
    return [
        {
            "id": c.id,
            "ubid": c.ubid,
            "field": c.field,
            "source_a": c.source_a,
            "value_a": c.value_a,
            "timestamp_a": c.timestamp_a.isoformat() if c.timestamp_a else None,
            "source_b": c.source_b,
            "value_b": c.value_b,
            "timestamp_b": c.timestamp_b.isoformat() if c.timestamp_b else None,
            "resolution_policy": c.resolution_policy,
            "resolved_value": c.resolved_value,
            "winning_source": c.winning_source,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in db.query(Conflict).order_by(Conflict.created_at.desc()).all()
    ]


@router.get("/retry-queue")
def list_retry_queue(db: Session = Depends(get_db)):
    return [
        {
            "id": r.id,
            "request_id": r.request_id,
            "ubid": r.ubid,
            "source_system": r.source_system,
            "target_system": r.target_system,
            "payload": r.payload,
            "retry_count": r.retry_count,
            "max_retries": r.max_retries,
            "status": r.status,
            "error_message": r.error_message,
            "next_retry_at": r.next_retry_at.isoformat() if r.next_retry_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in db.query(RetryQueueItem).order_by(RetryQueueItem.created_at.desc()).all()
    ]


@router.get("/health")
def system_health(db: Session = Depends(get_db)):
    states = db.query(SyncState).all()
    health = {}
    for s in states:
        health[s.system_name] = {
            "is_healthy": s.is_healthy == "true",
            "last_poll_at": s.last_poll_at.isoformat() if s.last_poll_at else None,
            "last_successful_sync": s.last_successful_sync.isoformat() if s.last_successful_sync else None,
            "poll_count": s.poll_count,
        }
    return health


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "total_businesses": db.query(UBIDRegistry).count(),
        "total_audit_logs": db.query(AuditLog).count(),
        "total_conflicts": db.query(Conflict).count(),
        "pending_retries": db.query(RetryQueueItem).filter(RetryQueueItem.status == "PENDING").count(),
        "successful_syncs": db.query(AuditLog).filter(AuditLog.status == "SUCCESS").count(),
        "failed_syncs": db.query(AuditLog).filter(AuditLog.status == "FAILED").count(),
    }


# ── Demo trigger endpoints ───────────────────────────────────────────

@router.post("/demo/sws-to-departments")
def demo_sws_to_dept(db: Session = Depends(get_db)):
    """Demo Flow 1: Update address in SWS → propagates to Factory & Shop."""
    ubid = "UBID-1001"
    sws = db.query(SWSRecord).filter(SWSRecord.ubid == ubid).first()
    if not sws:
        return {"error": "Seed data missing"}

    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    new_addr = f"Mysore, KA (Updated {now_str})"
    
    sws.registered_address = new_addr
    sws.change_source = "DIRECT"
    sws.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "triggered", "flow": "SWS → Departments",
            "ubid": ubid, "field": "registered_address", "new_value": new_addr,
            "note": "Polling will detect and propagate within 5 seconds"}


@router.post("/demo/department-to-sws")
def demo_dept_to_sws(db: Session = Depends(get_db)):
    """Demo Flow 2: Update signatory in Factory → propagates to SWS & Shop."""
    ubid = "UBID-1001"
    fac = db.query(FactoryRecord).filter(FactoryRecord.business_id == ubid).first()
    if not fac:
        return {"error": "Seed data missing"}

    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    new_name = f"Suresh Kumar ({now_str})"
    
    fac.signatory_name = new_name
    fac.change_source = "DIRECT"
    fac.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "triggered", "flow": "Factory → SWS & Shop",
            "ubid": ubid, "field": "signatory_name", "new_value": new_name}


@router.post("/demo/conflict")
def demo_conflict(db: Session = Depends(get_db)):
    """Demo Flow 3: Simultaneous address updates in SWS and Factory."""
    ubid = "UBID-1002"
    now = datetime.now(timezone.utc)

    # SWS update
    sws = db.query(SWSRecord).filter(SWSRecord.ubid == ubid).first()
    if sws:
        sws.registered_address = "Hubli, Karnataka"
        sws.change_source = "DIRECT"
        sws.updated_at = now
        db.commit()

    # Factory update (slightly later — this one should win)
    fac = db.query(FactoryRecord).filter(FactoryRecord.business_id == ubid).first()
    if fac:
        fac.factory_addr = "Dharwad, Karnataka"
        fac.change_source = "DIRECT"
        fac.updated_at = now + timedelta(seconds=2)
        db.commit()

    return {"status": "triggered", "flow": "Conflict Detection",
            "ubid": ubid, "sws_value": "Hubli, Karnataka",
            "factory_value": "Dharwad, Karnataka",
            "expected_winner": "FACTORY (latest timestamp)"}


@router.post("/demo/retry")
def demo_retry(db: Session = Depends(get_db)):
    """Demo Flow 4: Enable Factory failures, then trigger SWS update."""
    from ..mock_systems import factory as fmod

    ubid = "UBID-1003"
    fmod._simulate_failure = True
    fmod._failure_countdown = 3

    sws = db.query(SWSRecord).filter(SWSRecord.ubid == ubid).first()
    if sws:
        sws.registered_address = "Mangalore, Karnataka"
        sws.change_source = "DIRECT"
        sws.updated_at = datetime.now(timezone.utc)
        db.commit()

    return {"status": "triggered", "flow": "Retry & Idempotency",
            "ubid": ubid, "factory_failures_remaining": 3,
            "note": "Factory will fail 3 times, then succeed on retry"}


@router.post("/demo/reset")
def demo_reset(db: Session = Depends(get_db)):
    """Reset all data to initial seed state."""
    from ..seed import seed_database
    # Clear operational tables
    db.query(AuditLog).delete()
    db.query(ProcessedRequest).delete()
    db.query(RetryQueueItem).delete()
    db.query(Conflict).delete()
    db.query(SyncState).delete()
    db.commit()

    # Re-seed
    seed_database(db, reset=True)
    return {"status": "reset_complete"}

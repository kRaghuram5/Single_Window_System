"""
Mock Factory & Boiler Department System.
Uses DIFFERENT field names than SWS to demonstrate schema heterogeneity.
  SWS field              → Factory field
  ubid                   → business_id
  business_name          → establishment_name
  registered_address     → factory_addr
  authorized_signatory   → signatory_name
  status                 → license_status
"""

import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FactoryRecord

router = APIRouter(prefix="/api/factory", tags=["Mock Factory Dept"])

# Toggleable failure simulation for Demo Flow 4
_simulate_failure = False
_failure_countdown = 0


class FactoryUpdate(BaseModel):
    business_id: str
    establishment_name: Optional[str] = None
    factory_addr: Optional[str] = None
    signatory_name: Optional[str] = None
    license_status: Optional[str] = None


def _record_to_dict(r: FactoryRecord) -> dict:
    return {
        "business_id": r.business_id,
        "establishment_name": r.establishment_name,
        "factory_addr": r.factory_addr,
        "signatory_name": r.signatory_name,
        "license_status": r.license_status,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.post("/update")
def update_factory(req: FactoryUpdate, source: str = "DIRECT", db: Session = Depends(get_db)):
    global _simulate_failure, _failure_countdown

    # Simulate transient API failure for retry demo
    if _simulate_failure and source == "MIDDLEWARE":
        _failure_countdown -= 1
        if _failure_countdown <= 0:
            _simulate_failure = False
        raise HTTPException(503, "Factory system temporarily unavailable (simulated)")

    record = db.query(FactoryRecord).filter(FactoryRecord.business_id == req.business_id).first()
    if not record:
        raise HTTPException(404, f"business_id {req.business_id} not found in Factory system")

    changed = {}
    for field in ("establishment_name", "factory_addr", "signatory_name", "license_status"):
        val = getattr(req, field, None)
        if val is not None:
            old = getattr(record, field)
            if old != val:
                setattr(record, field, val)
                changed[field] = {"old": old, "new": val}

    record.change_source = source
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return {"status": "updated", "business_id": req.business_id, "changed_fields": changed}


@router.get("/factory/{ubid}")
def get_factory(ubid: str, db: Session = Depends(get_db)):
    record = db.query(FactoryRecord).filter(FactoryRecord.business_id == ubid).first()
    if not record:
        raise HTTPException(404, f"business_id {ubid} not found")
    return _record_to_dict(record)


@router.get("/changes")
def get_changes(since: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FactoryRecord).filter(FactoryRecord.change_source == "DIRECT")
    if since:
        query = query.filter(FactoryRecord.updated_at > datetime.fromisoformat(since))
    return [_record_to_dict(r) for r in query.all()]


@router.get("/all")
def get_all(db: Session = Depends(get_db)):
    return [_record_to_dict(r) for r in db.query(FactoryRecord).all()]


@router.post("/simulate-failure")
def toggle_failure(fail_count: int = 3):
    """Enable transient failures for the next N middleware-sourced requests."""
    global _simulate_failure, _failure_countdown
    _simulate_failure = True
    _failure_countdown = fail_count
    return {"status": "failure_simulation_enabled", "remaining_failures": fail_count}

"""
Mock SWS (Single Window System) — Karnataka's citizen-facing portal.
Schema uses canonical government field names.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SWSRecord

router = APIRouter(prefix="/api/sws", tags=["Mock SWS"])


class SWSUpdate(BaseModel):
    ubid: str
    business_name: Optional[str] = None
    registered_address: Optional[str] = None
    authorized_signatory: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = None
    _source: Optional[str] = "DIRECT"


def _record_to_dict(r: SWSRecord) -> dict:
    return {
        "ubid": r.ubid,
        "business_name": r.business_name,
        "registered_address": r.registered_address,
        "authorized_signatory": r.authorized_signatory,
        "contact_email": r.contact_email,
        "status": r.status,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.post("/update-business")
def update_business(req: SWSUpdate, source: str = "DIRECT", db: Session = Depends(get_db)):
    """Update a business record in SWS. source=MIDDLEWARE when called by the sync engine."""
    record = db.query(SWSRecord).filter(SWSRecord.ubid == req.ubid).first()
    if not record:
        raise HTTPException(404, f"UBID {req.ubid} not found in SWS")

    changed = {}
    for field in ("business_name", "registered_address", "authorized_signatory", "contact_email", "status"):
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
    return {"status": "updated", "ubid": req.ubid, "changed_fields": changed}


@router.get("/business/{ubid}")
def get_business(ubid: str, db: Session = Depends(get_db)):
    record = db.query(SWSRecord).filter(SWSRecord.ubid == ubid).first()
    if not record:
        raise HTTPException(404, f"UBID {ubid} not found in SWS")
    return _record_to_dict(record)


@router.get("/changes")
def get_changes(since: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns DIRECT (user-initiated) changes since a given ISO timestamp."""
    query = db.query(SWSRecord).filter(SWSRecord.change_source == "DIRECT")
    if since:
        query = query.filter(SWSRecord.updated_at > datetime.fromisoformat(since))
    return [_record_to_dict(r) for r in query.all()]


@router.get("/all")
def get_all(db: Session = Depends(get_db)):
    return [_record_to_dict(r) for r in db.query(SWSRecord).all()]

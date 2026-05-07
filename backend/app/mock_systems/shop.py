"""
Mock Shop & Commercial Establishment System.
Uses yet another schema to demonstrate heterogeneity.
  SWS field              → Shop field
  ubid                   → shop_ubid
  business_name          → shop_name
  registered_address     → shop_location
  authorized_signatory   → owner_name
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ShopRecord

router = APIRouter(prefix="/api/shop", tags=["Mock Shop Establishment"])


class ShopUpdate(BaseModel):
    shop_ubid: str
    shop_name: Optional[str] = None
    shop_location: Optional[str] = None
    owner_name: Optional[str] = None


def _record_to_dict(r: ShopRecord) -> dict:
    return {
        "shop_ubid": r.shop_ubid,
        "shop_name": r.shop_name,
        "shop_location": r.shop_location,
        "owner_name": r.owner_name,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.post("/update")
def update_shop(req: ShopUpdate, source: str = "DIRECT", db: Session = Depends(get_db)):
    record = db.query(ShopRecord).filter(ShopRecord.shop_ubid == req.shop_ubid).first()
    if not record:
        raise HTTPException(404, f"shop_ubid {req.shop_ubid} not found in Shop system")

    changed = {}
    for field in ("shop_name", "shop_location", "owner_name"):
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
    return {"status": "updated", "shop_ubid": req.shop_ubid, "changed_fields": changed}


@router.get("/shop/{ubid}")
def get_shop(ubid: str, db: Session = Depends(get_db)):
    record = db.query(ShopRecord).filter(ShopRecord.shop_ubid == ubid).first()
    if not record:
        raise HTTPException(404, f"shop_ubid {ubid} not found")
    return _record_to_dict(record)


@router.get("/changes")
def get_changes(since: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ShopRecord).filter(ShopRecord.change_source == "DIRECT")
    if since:
        query = query.filter(ShopRecord.updated_at > datetime.fromisoformat(since))
    return [_record_to_dict(r) for r in query.all()]


@router.get("/all")
def get_all(db: Session = Depends(get_db)):
    return [_record_to_dict(r) for r in db.query(ShopRecord).all()]

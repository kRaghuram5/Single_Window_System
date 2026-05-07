"""
UBID Resolver
──────────────
Maintains the UBID → system-record mapping registry.
Given a UBID, tells the middleware which systems hold a record
for that business so propagation targets can be determined.
"""

from sqlalchemy.orm import Session
from ..models import UBIDRegistry


def get_target_systems(ubid: str, source_system: str, db: Session) -> list[str]:
    """Return the list of systems that hold a record for *ubid*,
    EXCLUDING the source_system (we don't echo back)."""
    reg = db.query(UBIDRegistry).filter(UBIDRegistry.ubid == ubid).first()
    if not reg:
        return []

    targets = []
    if reg.sws_id is not None and source_system != "SWS":
        targets.append("SWS")
    if reg.factory_id is not None and source_system != "FACTORY":
        targets.append("FACTORY")
    if reg.shop_id is not None and source_system != "SHOP":
        targets.append("SHOP")
    return targets


def register_ubid(ubid: str, db: Session, sws_id=None, factory_id=None, shop_id=None):
    """Create or update a registry entry for a UBID."""
    reg = db.query(UBIDRegistry).filter(UBIDRegistry.ubid == ubid).first()
    if not reg:
        reg = UBIDRegistry(ubid=ubid)
        db.add(reg)

    if sws_id is not None:
        reg.sws_id = sws_id
    if factory_id is not None:
        reg.factory_id = factory_id
    if shop_id is not None:
        reg.shop_id = shop_id
    db.commit()
    return reg


def get_all_ubids(db: Session) -> list[str]:
    return [r.ubid for r in db.query(UBIDRegistry).all()]

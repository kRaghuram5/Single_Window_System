"""
Seed data — populates mock systems with 5 Karnataka businesses.
Each business has a record in all three systems with consistent data
but system-specific field names.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import SWSRecord, FactoryRecord, ShopRecord, UBIDRegistry, SyncState

SEED_BUSINESSES = [
    {
        "ubid": "UBID-1001",
        "business_name": "Bangalore Tech Solutions Pvt Ltd",
        "registered_address": "MG Road, Bangalore, Karnataka",
        "authorized_signatory": "Ramesh Kulkarni",
        "contact_email": "ramesh@bts.co.in",
        "status": "ACTIVE",
    },
    {
        "ubid": "UBID-1002",
        "business_name": "Mysore Silk Emporium",
        "registered_address": "Sayyaji Rao Road, Mysore, Karnataka",
        "authorized_signatory": "Lakshmi Devi",
        "contact_email": "lakshmi@silkemporium.in",
        "status": "ACTIVE",
    },
    {
        "ubid": "UBID-1003",
        "business_name": "Hubli Engineering Works",
        "registered_address": "Lamington Road, Hubli, Karnataka",
        "authorized_signatory": "Vikas Patil",
        "contact_email": "vikas@hew.co.in",
        "status": "ACTIVE",
    },
    {
        "ubid": "UBID-1004",
        "business_name": "Udupi Restaurant Chain",
        "registered_address": "Car Street, Udupi, Karnataka",
        "authorized_signatory": "Ganesh Shetty",
        "contact_email": "ganesh@udupichain.in",
        "status": "ACTIVE",
    },
    {
        "ubid": "UBID-1005",
        "business_name": "Belgaum Auto Components",
        "registered_address": "Khanapur Road, Belgaum, Karnataka",
        "authorized_signatory": "Ashok Desai",
        "contact_email": "ashok@bac.co.in",
        "status": "ACTIVE",
    },
]


def seed_database(db: Session, reset: bool = False):
    """Insert seed data. If reset=True, deletes existing records first."""
    if reset:
        db.query(SWSRecord).delete()
        db.query(FactoryRecord).delete()
        db.query(ShopRecord).delete()
        db.query(UBIDRegistry).delete()
        db.commit()

    for biz in SEED_BUSINESSES:
        # Skip if already exists
        if db.query(SWSRecord).filter(SWSRecord.ubid == biz["ubid"]).first():
            continue

        now = datetime.now(timezone.utc)

        # SWS record (canonical field names)
        sws = SWSRecord(
            ubid=biz["ubid"],
            business_name=biz["business_name"],
            registered_address=biz["registered_address"],
            authorized_signatory=biz["authorized_signatory"],
            contact_email=biz["contact_email"],
            status=biz["status"],
            change_source="SEED",
            updated_at=now,
            created_at=now,
        )
        db.add(sws)
        db.flush()

        # Factory record (different field names!)
        fac = FactoryRecord(
            business_id=biz["ubid"],
            establishment_name=biz["business_name"],
            factory_addr=biz["registered_address"],
            signatory_name=biz["authorized_signatory"],
            license_status=biz["status"],
            change_source="SEED",
            updated_at=now,
            created_at=now,
        )
        db.add(fac)
        db.flush()

        # Shop record (yet another schema!)
        shop = ShopRecord(
            shop_ubid=biz["ubid"],
            shop_name=biz["business_name"],
            shop_location=biz["registered_address"],
            owner_name=biz["authorized_signatory"],
            change_source="SEED",
            updated_at=now,
            created_at=now,
        )
        db.add(shop)
        db.flush()

        # UBID registry
        reg = UBIDRegistry(
            ubid=biz["ubid"],
            sws_id=sws.id,
            factory_id=fac.id,
            shop_id=shop.id,
        )
        db.add(reg)

    # Initialize sync state for each system
    for sys_name in ("SWS", "FACTORY", "SHOP"):
        if not db.query(SyncState).filter(SyncState.system_name == sys_name).first():
            db.add(SyncState(system_name=sys_name))

    db.commit()

"""
All SQLAlchemy models for UBID-Sync.
Separate tables per mock system + middleware operational tables.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ── Mock System Tables ──────────────────────────────────────────────

class SWSRecord(Base):
    """Karnataka Single Window System — canonical citizen-facing record."""
    __tablename__ = "sws_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ubid = Column(String, unique=True, nullable=False, index=True)
    business_name = Column(String)
    registered_address = Column(String)
    authorized_signatory = Column(String)
    contact_email = Column(String)
    status = Column(String, default="ACTIVE")
    change_source = Column(String, default="DIRECT")   # DIRECT | MIDDLEWARE
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)


class FactoryRecord(Base):
    """Factory & Boiler Department — different field names by design."""
    __tablename__ = "factory_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, unique=True, nullable=False, index=True)  # maps to UBID
    establishment_name = Column(String)
    factory_addr = Column(String)
    signatory_name = Column(String)
    license_status = Column(String, default="ACTIVE")
    change_source = Column(String, default="DIRECT")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)


class ShopRecord(Base):
    """Shop & Commercial Establishment — yet another schema."""
    __tablename__ = "shop_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_ubid = Column(String, unique=True, nullable=False, index=True)  # maps to UBID
    shop_name = Column(String)
    shop_location = Column(String)
    owner_name = Column(String)
    change_source = Column(String, default="DIRECT")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)


# ── Middleware Operational Tables ────────────────────────────────────

class UBIDRegistry(Base):
    """Maps a UBID to record IDs across all systems."""
    __tablename__ = "ubid_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ubid = Column(String, unique=True, nullable=False, index=True)
    sws_id = Column(Integer, nullable=True)
    factory_id = Column(Integer, nullable=True)
    shop_id = Column(Integer, nullable=True)


class AuditLog(Base):
    """Complete propagation history — the single source of truth for traceability."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False, index=True)
    ubid = Column(String, nullable=False, index=True)
    source_system = Column(String, nullable=False)
    target_system = Column(String, nullable=False)
    field_changed = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    status = Column(String, default="SUCCESS")       # SUCCESS | FAILED | RETRYING
    retry_count = Column(Integer, default=0)
    conflict_flag = Column(String, default="NONE")   # NONE | DETECTED | RESOLVED
    timestamp = Column(DateTime, default=_utcnow)


class ProcessedRequest(Base):
    """Idempotency ledger — prevents duplicate processing on retries."""
    __tablename__ = "processed_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, unique=True, nullable=False, index=True)
    ubid = Column(String)
    source_system = Column(String)
    processed_at = Column(DateTime, default=_utcnow)


class RetryQueueItem(Base):
    """Failed propagations waiting to be retried."""
    __tablename__ = "retry_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False, index=True)
    ubid = Column(String, nullable=False)
    source_system = Column(String)
    target_system = Column(String)
    payload = Column(Text)          # JSON-encoded update payload
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=5)
    status = Column(String, default="PENDING")  # PENDING | SUCCESS | EXHAUSTED
    error_message = Column(Text)
    next_retry_at = Column(DateTime)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Conflict(Base):
    """Records of detected concurrent-update conflicts and their resolutions."""
    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ubid = Column(String, nullable=False, index=True)
    field = Column(String, nullable=False)
    source_a = Column(String)
    value_a = Column(String)
    timestamp_a = Column(DateTime)
    source_b = Column(String)
    value_b = Column(String)
    timestamp_b = Column(DateTime)
    resolution_policy = Column(String, default="LATEST_TIMESTAMP_WINS")
    resolved_value = Column(String)
    winning_source = Column(String)
    status = Column(String, default="RESOLVED")
    created_at = Column(DateTime, default=_utcnow)


class SyncState(Base):
    """Tracks per-system polling state for the middleware."""
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_name = Column(String, unique=True, nullable=False)
    last_poll_at = Column(DateTime)
    last_successful_sync = Column(DateTime)
    is_healthy = Column(String, default="true")
    poll_count = Column(Integer, default=0)

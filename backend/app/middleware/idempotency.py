"""
Idempotency Engine
──────────────────
Prevents duplicate processing when retries replay the same request_id.
Every processed canonical event is recorded; replays are silently skipped.
"""

from sqlalchemy.orm import Session
from ..models import ProcessedRequest


def is_duplicate(request_id: str, db: Session) -> bool:
    """Return True if this request_id has already been fully processed."""
    return db.query(ProcessedRequest).filter(
        ProcessedRequest.request_id == request_id
    ).first() is not None


def mark_processed(request_id: str, ubid: str, source_system: str, db: Session):
    """Record a request_id as processed."""
    if not is_duplicate(request_id, db):
        db.add(ProcessedRequest(
            request_id=request_id,
            ubid=ubid,
            source_system=source_system,
        ))
        db.commit()

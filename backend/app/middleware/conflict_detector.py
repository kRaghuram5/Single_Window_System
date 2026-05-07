"""
Conflict Detection Engine
─────────────────────────
If two updates for the same UBID+field arrive from different sources
within CONFLICT_WINDOW_SECONDS, a conflict is flagged.

Prototype policy: LATEST_TIMESTAMP_WINS.
All conflicts are recorded for auditability.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from ..models import AuditLog, Conflict

CONFLICT_WINDOW_SECONDS = 30


def check_and_resolve(
    ubid: str,
    field: str,
    new_value: str,
    source_system: str,
    event_time: datetime,
    db: Session,
) -> dict | None:
    """Check for a conflicting recent update.

    Returns a conflict dict if one was detected (and resolved),
    or None if there is no conflict.
    """
    window_start = event_time - timedelta(seconds=CONFLICT_WINDOW_SECONDS)

    recent = (
        db.query(AuditLog)
        .filter(
            AuditLog.ubid == ubid,
            AuditLog.field_changed == field,
            AuditLog.source_system != source_system,
            AuditLog.timestamp >= window_start,
            AuditLog.status == "SUCCESS",
        )
        .order_by(AuditLog.timestamp.desc())
        .first()
    )

    if not recent:
        return None

    # We have a conflict — apply LATEST_TIMESTAMP_WINS
    if event_time >= recent.timestamp:
        winning_source = source_system
        resolved_value = new_value
    else:
        winning_source = recent.source_system
        resolved_value = recent.new_value

    conflict = Conflict(
        ubid=ubid,
        field=field,
        source_a=recent.source_system,
        value_a=recent.new_value,
        timestamp_a=recent.timestamp,
        source_b=source_system,
        value_b=new_value,
        timestamp_b=event_time,
        resolution_policy="LATEST_TIMESTAMP_WINS",
        resolved_value=resolved_value,
        winning_source=winning_source,
        status="RESOLVED",
    )
    db.add(conflict)
    db.commit()
    db.refresh(conflict)

    return {
        "conflict_id": conflict.id,
        "winning_source": winning_source,
        "resolved_value": resolved_value,
        "should_propagate": winning_source == source_system,
    }

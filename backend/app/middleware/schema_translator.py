"""
Schema Translation Engine
─────────────────────────
Adapter-based bidirectional mapping between each department's native schema
and a canonical (SWS-like) schema.  Adding a new department is just adding
a new pair of dictionaries — no existing code changes required.
"""

# ── Canonical field names (SWS is treated as canonical) ──────────────

CANONICAL_FIELDS = [
    "ubid",
    "business_name",
    "registered_address",
    "authorized_signatory",
    "contact_email",
    "status",
]

# ── Per-system mapping dicts ─────────────────────────────────────────
# SYSTEM_TO_CANONICAL:  department field  → canonical field
# CANONICAL_TO_SYSTEM:  canonical field   → department field

FACTORY_TO_CANONICAL = {
    "business_id":        "ubid",
    "establishment_name": "business_name",
    "factory_addr":       "registered_address",
    "signatory_name":     "authorized_signatory",
    "license_status":     "status",
}
CANONICAL_TO_FACTORY = {v: k for k, v in FACTORY_TO_CANONICAL.items()}

SHOP_TO_CANONICAL = {
    "shop_ubid":    "ubid",
    "shop_name":    "business_name",
    "shop_location":"registered_address",
    "owner_name":   "authorized_signatory",
}
CANONICAL_TO_SHOP = {v: k for k, v in SHOP_TO_CANONICAL.items()}

# SWS is already canonical — identity mapping
SWS_TO_CANONICAL = {f: f for f in CANONICAL_FIELDS}
CANONICAL_TO_SWS = {f: f for f in CANONICAL_FIELDS}

# ── Registry of all adapters (keyed by system name) ──────────────────

_TO_CANONICAL = {
    "SWS":     SWS_TO_CANONICAL,
    "FACTORY": FACTORY_TO_CANONICAL,
    "SHOP":    SHOP_TO_CANONICAL,
}

_FROM_CANONICAL = {
    "SWS":     CANONICAL_TO_SWS,
    "FACTORY": CANONICAL_TO_FACTORY,
    "SHOP":    CANONICAL_TO_SHOP,
}

# UBID field name per system (the key that identifies the business)
UBID_FIELD = {
    "SWS":     "ubid",
    "FACTORY": "business_id",
    "SHOP":    "shop_ubid",
}


# ── Public API ───────────────────────────────────────────────────────

def to_canonical(system: str, record: dict) -> dict:
    """Translate a department record into canonical field names."""
    mapping = _TO_CANONICAL.get(system)
    if not mapping:
        raise ValueError(f"No adapter registered for system '{system}'")
    return {mapping[k]: v for k, v in record.items() if k in mapping}


def from_canonical(system: str, canonical: dict) -> dict:
    """Translate a canonical record into a department's native field names."""
    mapping = _FROM_CANONICAL.get(system)
    if not mapping:
        raise ValueError(f"No adapter registered for system '{system}'")
    return {mapping[k]: v for k, v in canonical.items() if k in mapping}


def translate_field(source_system: str, target_system: str, field_name: str) -> str | None:
    """Map a single field name from one system's schema to another's."""
    to_can = _TO_CANONICAL.get(source_system, {})
    from_can = _FROM_CANONICAL.get(target_system, {})
    canonical = to_can.get(field_name)
    if canonical is None:
        return None
    return from_can.get(canonical)


def get_ubid_from_record(system: str, record: dict) -> str | None:
    """Extract the UBID value from a system-specific record."""
    field = UBID_FIELD.get(system)
    return record.get(field) if field else None


def get_all_systems() -> list[str]:
    return list(_TO_CANONICAL.keys())

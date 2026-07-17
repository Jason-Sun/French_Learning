"""Canonical identity registry helpers; importers map records through this module."""

from __future__ import annotations

import sqlite3
import uuid


NAMESPACE = uuid.UUID("d532a99b-399c-5db0-97e4-6a32e63ac4b7")


def canonical_uuid(identity_key: str) -> str:
    """Return the permanent UUIDv5 for a source-independent identity key."""
    return str(uuid.uuid5(NAMESPACE, f"liens:object:{identity_key}"))


def resolve_canonical_id(db: sqlite3.Connection, identity_key: str) -> str | None:
    """Resolve an existing canonical identity; importers must not mint IDs directly."""
    row = db.execute("SELECT canonical_id FROM canonical_objects WHERE identity_key=?", (identity_key,)).fetchone()
    return row[0] if row else None

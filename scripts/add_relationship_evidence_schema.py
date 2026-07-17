#!/usr/bin/env python3
"""Add independent provenance for canonical graph relationships."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


MIGRATION_ID = "20260717_relationship_evidence_schema"
SCHEMA = """
CREATE TABLE IF NOT EXISTS relationship_evidence (
  relationship_id TEXT NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  evidence_role TEXT NOT NULL DEFAULT 'asserts',
  confidence REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY(relationship_id, source_record_id, evidence_role)
);
CREATE INDEX IF NOT EXISTS idx_relationship_evidence_source
  ON relationship_evidence(source_record_id);
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    database = sqlite3.connect(args.database)
    database.execute("PRAGMA foreign_keys=ON")
    database.executescript(SCHEMA)
    database.execute(
        """INSERT OR IGNORE INTO schema_migrations(id, checksum, description)
           VALUES (?, ?, ?)""",
        (
            MIGRATION_ID,
            hashlib.sha256(SCHEMA.encode()).hexdigest(),
            "Evidence links for typed canonical graph relationships.",
        ),
    )
    database.execute(
        """INSERT INTO metadata(key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (
            "relationship_evidence_model",
            "New canonical relationship imports must record immutable relationship_evidence; legacy edges remain a compatibility backlog.",
        ),
    )
    database.commit()
    print("Relationship evidence schema is ready.")


if __name__ == "__main__":
    main()

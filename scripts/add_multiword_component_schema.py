#!/usr/bin/env python3
"""Add ordered, source-evidenced components for multi-word Language Objects."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


MIGRATION_ID = "20260717_multiword_component_schema"
SCHEMA = """
CREATE TABLE IF NOT EXISTS multiword_components (
  parent_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  position INTEGER NOT NULL CHECK(position >= 1),
  component_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE RESTRICT,
  display_surface TEXT NOT NULL,
  PRIMARY KEY(parent_object_id, position)
);
CREATE INDEX IF NOT EXISTS idx_multiword_components_component
  ON multiword_components(component_object_id);
CREATE TABLE IF NOT EXISTS multiword_component_evidence (
  parent_object_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  source_surface TEXT NOT NULL,
  PRIMARY KEY(parent_object_id, position, source_record_id),
  FOREIGN KEY(parent_object_id, position)
    REFERENCES multiword_components(parent_object_id, position) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_multiword_component_evidence_source
  ON multiword_component_evidence(source_record_id);
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
            "Ordered component structure and source evidence for expressions, idioms, collocations, and other multi-word objects.",
        ),
    )
    database.execute(
        """INSERT INTO metadata(key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (
            "multiword_component_model",
            "A multi-word object has ordered component Language Objects with source-specific component evidence; contains edges remain the graph-navigation projection.",
        ),
    )
    database.commit()
    print("Multi-word component schema is ready.")


if __name__ == "__main__":
    main()

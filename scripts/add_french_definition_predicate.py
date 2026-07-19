#!/usr/bin/env python3
"""Register French source definitions as an evidence-backed lexical fact."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


MIGRATION_ID = "20260719_french_definition_predicate"
SCHEMA = """
INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES
  ('french_definition','text','French source definition',
   'An evidence-backed French-language definition for a lexical sense. It is not an English gloss or an AI learning resource.');
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
            "French source-definition predicate for evidence-backed lexical senses.",
        ),
    )
    database.commit()
    print("French definition predicate is ready.")


if __name__ == "__main__":
    main()

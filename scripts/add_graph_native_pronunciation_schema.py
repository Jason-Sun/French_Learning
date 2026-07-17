#!/usr/bin/env python3
"""Upgrade legacy Liens pronunciation records into graph-native Language Objects."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from pronunciation_graph import sync_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.execute("PRAGMA foreign_keys = ON")
    count = sync_graph(db)
    db.execute(
        "INSERT INTO metadata(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("schema_version", "5"),
    )
    db.execute(
        "INSERT INTO metadata(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("pronunciation_model", "graph-native Pronunciation Objects linked with has_pronunciation"),
    )
    db.commit()
    print(f"Graph-native pronunciation schema ready; synchronized {count} records.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Add source-independent identity, facts/evidence, and Learning Layer tables.

This is an additive compatibility migration. Existing Language Object IDs remain
usable by the browser while ``canonical_objects.canonical_id`` becomes the
permanent external/import identity.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

import uuid

from canonical_identity import NAMESPACE, canonical_uuid

MIGRATION_ID = "20260717_canonical_knowledge_layer"

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  checksum TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS canonical_objects (
  canonical_id TEXT PRIMARY KEY,
  language_object_id TEXT NOT NULL UNIQUE REFERENCES language_objects(id) ON DELETE RESTRICT,
  object_type_code TEXT NOT NULL REFERENCES object_types(code),
  identity_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS canonical_identity_aliases (
  identity_key TEXT PRIMARY KEY, canonical_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
  reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS source_catalogs (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, homepage_url TEXT, license TEXT NOT NULL,
  attribution_text TEXT NOT NULL, replacement_policy TEXT NOT NULL DEFAULT 'replaceable'
);
CREATE TABLE IF NOT EXISTS source_releases (
  id TEXT PRIMARY KEY, catalog_id TEXT NOT NULL REFERENCES source_catalogs(id),
  release_label TEXT NOT NULL, artifact_uri TEXT, sha256 TEXT, scope_description TEXT,
  released_at TEXT, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(catalog_id, release_label)
);
CREATE TABLE IF NOT EXISTS import_runs (
  id TEXT PRIMARY KEY, release_id TEXT NOT NULL REFERENCES source_releases(id),
  importer_name TEXT NOT NULL, importer_version TEXT NOT NULL, configuration_hash TEXT,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_records (
  id TEXT PRIMARY KEY, release_id TEXT NOT NULL REFERENCES source_releases(id),
  external_key TEXT NOT NULL, record_kind TEXT NOT NULL, content_hash TEXT,
  UNIQUE(release_id, external_key, record_kind)
);
CREATE TABLE IF NOT EXISTS import_record_mappings (
  import_run_id TEXT NOT NULL REFERENCES import_runs(id),
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  canonical_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id),
  mapping_kind TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY(import_run_id, source_record_id, canonical_id, mapping_kind)
);
CREATE TABLE IF NOT EXISTS import_exclusions (
  import_run_id TEXT NOT NULL REFERENCES import_runs(id),
  source_record_id TEXT NOT NULL REFERENCES source_records(id), reason_code TEXT NOT NULL,
  explanation TEXT, PRIMARY KEY(import_run_id, source_record_id)
);
CREATE TABLE IF NOT EXISTS fact_predicates (
  code TEXT PRIMARY KEY, value_kind TEXT NOT NULL CHECK(value_kind IN ('code','number','text','object')),
  label TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS canonical_facts (
  id TEXT PRIMARY KEY, canonical_subject_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id),
  predicate_code TEXT NOT NULL REFERENCES fact_predicates(code), lifecycle TEXT NOT NULL DEFAULT 'canonical',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS fact_code_values (
  fact_id TEXT PRIMARY KEY REFERENCES canonical_facts(id) ON DELETE CASCADE, value_code TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_number_values (
  fact_id TEXT PRIMARY KEY REFERENCES canonical_facts(id) ON DELETE CASCADE, value_number REAL NOT NULL, unit_code TEXT
);
CREATE TABLE IF NOT EXISTS fact_text_values (
  fact_id TEXT PRIMARY KEY REFERENCES canonical_facts(id) ON DELETE CASCADE, language_code TEXT, value_text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_object_values (
  fact_id TEXT PRIMARY KEY REFERENCES canonical_facts(id) ON DELETE CASCADE,
  value_canonical_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id)
);
CREATE TABLE IF NOT EXISTS fact_evidence (
  fact_id TEXT NOT NULL REFERENCES canonical_facts(id) ON DELETE CASCADE,
  source_record_id TEXT NOT NULL REFERENCES source_records(id), evidence_role TEXT NOT NULL DEFAULT 'asserts',
  confidence REAL NOT NULL DEFAULT 1.0, PRIMARY KEY(fact_id, source_record_id, evidence_role)
);
CREATE TABLE IF NOT EXISTS learning_resources (
  resource_object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
  authoring_mode TEXT NOT NULL CHECK(authoring_mode IN ('human','teacher','ai','imported')),
  lifecycle TEXT NOT NULL CHECK(lifecycle IN ('draft','reviewed','published','deprecated')),
  source_release_id TEXT REFERENCES source_releases(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS learning_resource_links (
  resource_object_id TEXT NOT NULL REFERENCES learning_resources(resource_object_id) ON DELETE CASCADE,
  canonical_object_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id), role_code TEXT NOT NULL,
  PRIMARY KEY(resource_object_id, canonical_object_id, role_code)
);
CREATE TABLE IF NOT EXISTS learning_resource_texts (
  id TEXT PRIMARY KEY, resource_object_id TEXT NOT NULL REFERENCES learning_resources(resource_object_id) ON DELETE CASCADE,
  language_code TEXT NOT NULL, content_role TEXT NOT NULL, content_text TEXT NOT NULL,
  UNIQUE(resource_object_id, language_code, content_role)
);
"""

PREDICATES = [
    ("part_of_speech", "code", "Part of speech", "Grammatical category of a lexical object."),
    ("cefr_level", "code", "CEFR level", "Source-supported CEFR classification."),
    ("frequency_per_million", "number", "Frequency", "Frequency per million tokens."),
    ("grammatical_gender", "code", "Grammatical gender", "Inherent grammatical gender."),
]


def stable_uuid(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def identity_key(row: sqlite3.Row, owner_canonical_id: str | None = None, features: sqlite3.Row | None = None) -> str:
    base = f"fr|{row['type_code']}|{row['part_of_speech'] or ''}|{row['normalized_form']}"
    if row["type_code"] != "inflected_form":
        if row["type_code"] != "pronunciation" or not owner_canonical_id:
            return base
        return base + "|owner=" + owner_canonical_id
    if not owner_canonical_id:
        return base + "|unresolved-owner"
    feature_key = "|".join(str(features[column] or "") for column in ("mood", "tense", "person", "number", "gender")) if features else ""
    return base + "|owner=" + owner_canonical_id + "|features=" + feature_key


def insert_fact(db: sqlite3.Connection, subject: str, predicate: str, value: object, source_record: str) -> None:
    kind = next(item[1] for item in PREDICATES if item[0] == predicate)
    serialized = str(value)
    fact_id = stable_uuid("fact", f"{subject}|{predicate}|{serialized}")
    db.execute(
        "INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)",
        (fact_id, subject, predicate),
    )
    if kind == "number":
        db.execute("INSERT OR IGNORE INTO fact_number_values(fact_id,value_number,unit_code) VALUES (?,?,'per_million')", (fact_id, value))
    else:
        db.execute("INSERT OR IGNORE INTO fact_code_values(fact_id,value_code) VALUES (?,?)", (fact_id, serialized))
    db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id) VALUES (?,?)", (fact_id, source_record))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    checksum = hashlib.sha256(SCHEMA.encode()).hexdigest()
    db.execute("INSERT OR IGNORE INTO schema_migrations(id,checksum,description) VALUES (?,?,?)", (MIGRATION_ID, checksum, "Source-independent canonical identity, facts/evidence, and Learning Layer."))
    db.executemany("INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)", PREDICATES)

    # Existing source rows become catalog/release metadata. The fallback release
    # is only a bootstrap provenance record; future importers use real releases.
    for source in db.execute("SELECT * FROM sources"):
        db.execute("INSERT OR IGNORE INTO source_catalogs VALUES (?,?,?,?,?,?)", (source["id"], source["name"], source["url"], source["license"], source["citation"], "replaceable"))
        db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,scope_description) VALUES (?,?,?,?,?)", (f"legacy:{source['id']}", source["id"], "legacy-unversioned", source["url"], "Migrated legacy Liens graph metadata."))
    db.execute("INSERT OR IGNORE INTO source_catalogs VALUES ('liens-legacy-bootstrap','Liens legacy bootstrap',NULL,'Internal migration metadata','Legacy graph values were converted during the canonical-layer migration.','replaceable')")
    db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,scope_description) VALUES ('legacy:liens-legacy-bootstrap','liens-legacy-bootstrap','2026-07-17','Fallback provenance for legacy rows without a source.')")
    # Correct an early single-run bootstrap if this migration is re-applied.
    # A production import run belongs to exactly one source release.
    db.execute("DELETE FROM import_record_mappings WHERE import_run_id='legacy-canonical-bootstrap'")
    db.execute("DELETE FROM import_runs WHERE id='legacy-canonical-bootstrap'")

    rows = list(db.execute("SELECT * FROM language_objects ORDER BY id"))
    owner_ids = {r["source_object_id"]: r["target_object_id"] for r in db.execute("SELECT source_object_id,target_object_id FROM relationships WHERE relationship_type_code='inflected_form_of'")}
    pronunciation_owners = {r["target_object_id"]: r["source_object_id"] for r in db.execute("SELECT source_object_id,target_object_id FROM relationships WHERE relationship_type_code='has_pronunciation'")}
    form_features = {row["object_id"]: row for row in db.execute("SELECT * FROM form_features")}
    canonical_by_object: dict[str, str] = {}
    # Register owners first, then forms, then pronunciation nodes. Neither
    # form nor pronunciation identity may depend on a legacy runtime ID.
    ordered_rows = [
        *filter(lambda item: item["type_code"] not in ("inflected_form", "pronunciation"), rows),
        *filter(lambda item: item["type_code"] == "inflected_form", rows),
        *filter(lambda item: item["type_code"] == "pronunciation", rows),
    ]
    for row in ordered_rows:
        owner_legacy_id = owner_ids.get(row["id"]) if row["type_code"] == "inflected_form" else pronunciation_owners.get(row["id"])
        owner_canonical_id = canonical_by_object.get(owner_legacy_id or "")
        key = identity_key(row, owner_canonical_id, form_features.get(row["id"]))
        canonical_id = canonical_uuid(key)
        canonical_by_object[row["id"]] = canonical_id
        db.execute("INSERT OR IGNORE INTO canonical_objects VALUES (?,?,?,?,CURRENT_TIMESTAMP)", (canonical_id, row["id"], row["type_code"], key))
        source_key = row["source_id"] or "liens-legacy-bootstrap"
        release = f"legacy:{source_key}"
        run_id = f"legacy-canonical-bootstrap:{source_key}"
        db.execute("INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,status,completed_at) VALUES (?,?, 'add_canonical_knowledge_layer','1','completed',CURRENT_TIMESTAMP)", (run_id, release))
        record_id = stable_uuid("source-record", f"{release}|{row['id']}")
        db.execute("INSERT OR IGNORE INTO source_records VALUES (?,?,?,?,?)", (record_id, release, row["id"], "legacy_object_metadata", hashlib.sha256(row["id"].encode()).hexdigest()))
        db.execute("INSERT OR IGNORE INTO import_record_mappings VALUES (?,?,?, 'identity',1.0)", (run_id, record_id, canonical_id))
        if row["part_of_speech"]:
            insert_fact(db, canonical_id, "part_of_speech", row["part_of_speech"], record_id)
        if row["cefr_level"]:
            insert_fact(db, canonical_id, "cefr_level", row["cefr_level"], record_id)
        if row["frequency_per_million"] is not None:
            insert_fact(db, canonical_id, "frequency_per_million", row["frequency_per_million"], record_id)

    # Existing structured teacher resources become general learning resources;
    # their content remains in legacy tables until its dedicated migration.
    for resource in db.execute("SELECT id,content_status,provenance FROM language_objects WHERE type_code='learning_resource'"):
        mode = "ai" if resource["provenance"] == "ai_enriched" else "imported"
        lifecycle = "draft" if resource["content_status"] in ("ai_enriched", "draft") else "reviewed"
        db.execute("INSERT OR IGNORE INTO learning_resources(resource_object_id,authoring_mode,lifecycle) VALUES (?,?,?)", (resource["id"], mode, lifecycle))
        for edge in db.execute("SELECT target_object_id FROM relationships WHERE source_object_id=? AND relationship_type_code='explains'", (resource["id"],)):
            target = canonical_by_object.get(edge["target_object_id"])
            if target:
                db.execute("INSERT OR IGNORE INTO learning_resource_links VALUES (?,?, 'explains')", (resource["id"], target))

    db.execute("INSERT INTO metadata(key,value) VALUES ('canonical_knowledge_layer','canonical_objects + canonical_facts + fact_evidence; importers map records, not identities') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    db.commit()
    print(f"Canonical layer ready: {len(canonical_by_object)} objects registered.")


if __name__ == "__main__":
    main()

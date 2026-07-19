#!/usr/bin/env python3
"""Create or evidence source-backed FLELex lexical identities for a CEFR scope.

This is the canonical lexical-baseline importer.  Unlike an enrichment importer,
it may create a *word* Language Object when its stable source-independent
identity does not exist yet.  It never creates senses, forms, or relationships.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
IMPORTER_NAME = "flelex_lexical_baseline"
IMPORTER_VERSION = "1"


@dataclass(frozen=True)
class Row:
    line: int
    lemma: str
    part_of_speech: str
    level: str
    frequency: float
    raw: dict[str, str]

    @property
    def external_key(self) -> str:
        return f"line:{self.line}"


def normalize(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def lexical_identity(lemma: str, part_of_speech: str) -> str:
    return f"fr|word|{part_of_speech}|{normalize(lemma)}"


def language_object_id(lemma: str, part_of_speech: str) -> str:
    # This is a storage adapter ID, not the permanent public identity. It keeps
    # compatibility with existing graph records while canonical UUID owns identity.
    return f"fr:word:{normalize(lemma)}:{part_of_speech.casefold()}"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not {"catalog", "release", "import"} <= set(manifest):
        raise ValueError("Manifest must contain catalog, release, and import sections.")
    return manifest


def selected_levels(manifest: dict) -> tuple[str, ...]:
    selection = manifest["import"].get("selection", {})
    raw = selection.get("levels") or [selection.get("level")]
    levels = tuple(sorted({str(value).strip() for value in raw if str(value).strip()}))
    if not levels or not set(levels) <= VALID_LEVELS:
        raise ValueError(f"Unsupported FLELex CEFR selection: {levels!r}")
    return levels


def selected_rows(source: Path, levels: set[str]) -> list[Row]:
    rows: list[Row] = []
    identities: set[tuple[str, str]] = set()
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"word", "tag", "freq_total", "level"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError(f"Unexpected FLELex columns; required {sorted(required)}.")
        for line, raw in enumerate(reader, start=2):
            level = raw["level"].strip()
            if level not in levels:
                continue
            lemma, pos = raw["word"].strip(), raw["tag"].strip()
            if not lemma or not pos:
                raise ValueError(f"Selected row {line} has no word or part of speech.")
            identity = (normalize(lemma), pos)
            if identity in identities:
                raise ValueError(f"Duplicate selected FLELex lexical identity: {lemma!r} ({pos})")
            identities.add(identity)
            rows.append(Row(line, lemma, pos, level, float(raw["freq_total"] or 0), raw))
    return rows


def insert_fact(db: sqlite3.Connection, canonical_id: str, predicate: str, value: str | float, record_id: str) -> None:
    fact_id = stable_id("fact", f"{canonical_id}|{predicate}|{value}")
    db.execute(
        "INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)",
        (fact_id, canonical_id, predicate),
    )
    if predicate == "frequency_per_million":
        db.execute(
            "INSERT OR IGNORE INTO fact_number_values(fact_id,value_number,unit_code) VALUES (?,?,'per_million')",
            (fact_id, value),
        )
    else:
        db.execute("INSERT OR IGNORE INTO fact_code_values(fact_id,value_code) VALUES (?,?)", (fact_id, value))
    db.execute(
        "INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1.0)",
        (fact_id, record_id),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    actual_hash = file_hash(args.source)
    expected_hash = manifest["release"]["sha256"]
    if actual_hash != expected_hash:
        raise ValueError(f"Source SHA-256 mismatch: expected {expected_hash}, got {actual_hash}")
    levels = selected_levels(manifest)
    rows = selected_rows(args.source, set(levels))

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    catalog, release = manifest["catalog"], manifest["release"]
    selection_id = "-".join(level.casefold() for level in levels)
    run_id = f"import:{release['id']}:{selection_id}-lexical-baseline"
    db.execute("BEGIN")
    try:
        db.execute(
            "INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES ('flelex-beacco-2025',?,?,?,?)",
            (catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
        )
        db.execute(
            "INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text) VALUES (?,?,?,?,?)",
            (catalog["id"], catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
        )
        db.execute(
            """INSERT OR IGNORE INTO source_releases
               (id,catalog_id,release_label,artifact_uri,sha256,scope_description)
               VALUES (?,?,?,?,?,?)""",
            (release["id"], catalog["id"], release["label"], release["artifact_uri"], release["sha256"], release["scope_description"]),
        )
        db.execute(
            """INSERT OR IGNORE INTO import_runs
               (id,release_id,importer_name,importer_version,status,completed_at)
               VALUES (?,?,?,?, 'completed',CURRENT_TIMESTAMP)""",
            (run_id, release["id"], IMPORTER_NAME, IMPORTER_VERSION),
        )
        for predicate, kind, label in (
            ("part_of_speech", "code", "Part of speech"),
            ("cefr_level", "code", "CEFR level"),
            ("frequency_per_million", "number", "Frequency"),
        ):
            db.execute(
                "INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)",
                (predicate, kind, label, "Source-backed FLELex lexical baseline fact."),
            )

        created = existing = mappings = 0
        for row in rows:
            identity = lexical_identity(row.lemma, row.part_of_speech)
            canonical_id = canonical_uuid(identity)
            record_id = stable_id("source-record", f"{release['id']}|{row.external_key}|lexical_row")
            raw_hash = hashlib.sha256(
                json.dumps(row.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            db.execute(
                """INSERT OR IGNORE INTO source_records
                   (id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)""",
                (record_id, release["id"], row.external_key, "lexical_row", raw_hash),
            )
            present = db.execute(
                "SELECT language_object_id FROM canonical_objects WHERE identity_key=?", (identity,)
            ).fetchone()
            if present:
                existing += 1
                object_id = present["language_object_id"]
                stored = db.execute(
                    "SELECT canonical_form,part_of_speech FROM language_objects WHERE id=?", (object_id,)
                ).fetchone()
                if not stored or normalize(stored["canonical_form"]) != normalize(row.lemma) or stored["part_of_speech"] != row.part_of_speech:
                    raise ValueError(f"Canonical identity collision for {row.lemma!r} ({row.part_of_speech})")
            else:
                object_id = language_object_id(row.lemma, row.part_of_speech)
                conflicting = db.execute("SELECT id FROM language_objects WHERE id=?", (object_id,)).fetchone()
                if conflicting:
                    raise ValueError(f"Storage object ID collision for {row.lemma!r} ({row.part_of_speech})")
                db.execute(
                    """INSERT INTO language_objects
                       (id,type_code,canonical_form,display_form,normalized_form,cefr_level,part_of_speech,
                        frequency_per_million,source_id,content_status,provenance)
                       VALUES (?,'word',?,?,?,?,?,?,'flelex-beacco-2025','metadata_ready','source_backed')""",
                    (object_id, row.lemma, row.lemma, normalize(row.lemma), row.level, row.part_of_speech, row.frequency),
                )
                db.execute("INSERT INTO learning_metadata(object_id) VALUES (?)", (object_id,))
                db.execute(
                    "INSERT INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?, 'word',?)",
                    (canonical_id, object_id, identity),
                )
                created += 1
            db.execute(
                """INSERT OR IGNORE INTO import_record_mappings
                   (import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'lexical_baseline',1.0)""",
                (run_id, record_id, canonical_id),
            )
            mappings += db.execute("SELECT changes()").fetchone()[0]
            insert_fact(db, canonical_id, "part_of_speech", row.part_of_speech, record_id)
            insert_fact(db, canonical_id, "cefr_level", row.level, record_id)
            insert_fact(db, canonical_id, "frequency_per_million", row.frequency, record_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {
        "release_id": release["id"],
        "source_sha256": actual_hash,
        "selection": {"levels": list(levels)},
        "selected_source_rows": len(rows),
        "canonical_word_objects_created": created,
        "existing_canonical_words_reused": existing,
        "source_record_mappings_created": mappings,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

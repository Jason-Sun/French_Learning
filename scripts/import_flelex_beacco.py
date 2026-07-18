#!/usr/bin/env python3
"""Import one hash-locked FLELex / Beacco release into the canonical graph.

The adapter does not create canonical Language Objects. It resolves each
source row through the canonical identity registry, records its source-native
evidence, and validates complete selected-release coverage before committing.
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

from canonical_identity import NAMESPACE, resolve_canonical_id


@dataclass(frozen=True)
class SourceRow:
    line_number: int
    lemma: str
    part_of_speech: str
    cefr_level: str
    frequency: float
    raw: dict[str, str]

    @property
    def external_key(self) -> str:
        return f"line:{self.line_number}"

    @property
    def content_hash(self) -> str:
        payload = json.dumps(self.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


def canonical_identity_key(lemma: str, part_of_speech: str) -> str:
    return f"fr|word|{part_of_speech}|{normalise(lemma)}"


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = ("catalog", "release", "import")
    if any(key not in manifest for key in required):
        raise ValueError("Manifest must contain catalog, release, and import sections.")
    return manifest


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_rows(source: Path, levels: set[str]) -> list[SourceRow]:
    rows: list[SourceRow] = []
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"word", "tag", "freq_total", "level"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(f"Unexpected FLELex columns; required {sorted(required)}.")
        for line_number, row in enumerate(reader, start=2):
            source_level = row["level"].strip()
            if source_level not in levels:
                continue
            lemma = row["word"].strip()
            pos = row["tag"].strip()
            if not lemma or not pos:
                raise ValueError(f"Selected row {line_number} has no lemma or part of speech.")
            rows.append(SourceRow(line_number, lemma, pos, source_level, float(row["freq_total"] or 0), row))
    return rows


def selected_levels(manifest: dict) -> tuple[str, ...]:
    selection = manifest["import"].get("selection", {})
    raw_levels = selection.get("levels") or [selection.get("level")]
    levels = tuple(sorted({str(level).strip() for level in raw_levels if str(level).strip()}))
    if not levels:
        raise ValueError("FLELex manifest must select at least one CEFR level.")
    if any(level not in {"A1", "A2", "B1", "B2", "C1", "C2"} for level in levels):
        raise ValueError(f"Unsupported FLELex CEFR level selection: {levels!r}")
    return levels


def fact_id_for_code(db: sqlite3.Connection, subject: str, predicate: str, value: str) -> str | None:
    row = db.execute(
        """SELECT f.id FROM canonical_facts f
           JOIN fact_code_values v ON v.fact_id=f.id
           WHERE f.canonical_subject_id=? AND f.predicate_code=? AND v.value_code=?""",
        (subject, predicate, value),
    ).fetchone()
    return row[0] if row else None


def fact_id_for_number(db: sqlite3.Connection, subject: str, predicate: str, value: float) -> str | None:
    row = db.execute(
        """SELECT f.id FROM canonical_facts f
           JOIN fact_number_values v ON v.fact_id=f.id
           WHERE f.canonical_subject_id=? AND f.predicate_code=?
             AND ABS(v.value_number - ?) < 0.000000001""",
        (subject, predicate, value),
    ).fetchone()
    return row[0] if row else None


def validate_rows(db: sqlite3.Connection, rows: list[SourceRow]) -> list[tuple[SourceRow, str, tuple[str, str, str]]]:
    seen: set[tuple[str, str]] = set()
    resolved: list[tuple[SourceRow, str, tuple[str, str, str]]] = []
    errors: list[str] = []
    for row in rows:
        source_identity = (row.lemma, row.part_of_speech)
        if source_identity in seen:
            errors.append(f"Duplicate source identity: {source_identity!r}")
            continue
        seen.add(source_identity)
        canonical_id = resolve_canonical_id(db, canonical_identity_key(row.lemma, row.part_of_speech))
        if canonical_id is None:
            errors.append(f"No canonical object for {row.lemma!r} ({row.part_of_speech})")
            continue
        fact_ids = (
            fact_id_for_code(db, canonical_id, "part_of_speech", row.part_of_speech),
            fact_id_for_code(db, canonical_id, "cefr_level", row.cefr_level),
            fact_id_for_number(db, canonical_id, "frequency_per_million", row.frequency),
        )
        if any(fact_id is None for fact_id in fact_ids):
            errors.append(f"Canonical fact mismatch for {row.lemma!r} ({row.part_of_speech})")
            continue
        resolved.append((row, canonical_id, fact_ids))
    if errors:
        sample = "\n".join(f"- {message}" for message in errors[:20])
        raise ValueError(f"FLELex preflight failed with {len(errors)} issue(s):\n{sample}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    actual_sha = hash_file(args.source)
    expected_sha = manifest["release"]["sha256"]
    if actual_sha != expected_sha:
        raise ValueError(f"Source SHA-256 mismatch: expected {expected_sha}, got {actual_sha}")

    levels = selected_levels(manifest)
    rows = selected_rows(args.source, set(levels))
    db = sqlite3.connect(args.database)
    db.execute("PRAGMA foreign_keys=ON")
    resolved = validate_rows(db, rows)

    catalog = manifest["catalog"]
    release = manifest["release"]
    selection_id = "-".join(level.casefold() for level in levels)
    run_id = f"import:{release['id']}:{selection_id}"
    db.execute("BEGIN")
    try:
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
               (id,release_id,importer_name,importer_version,configuration_hash,status,completed_at)
               VALUES (?,?,?,?,?,'completed',CURRENT_TIMESTAMP)""",
            (run_id, release["id"], manifest["import"]["adapter"], manifest["import"]["adapter_version"], hashlib.sha256(args.manifest.read_bytes()).hexdigest()),
        )
        for row, canonical_id, fact_ids in resolved:
            record_id = stable_id("source-record", f"{release['id']}|{row.external_key}|lexical_row")
            db.execute(
                "INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",
                (record_id, release["id"], row.external_key, "lexical_row", row.content_hash),
            )
            db.execute(
                """INSERT OR IGNORE INTO import_record_mappings
                   (import_run_id,source_record_id,canonical_id,mapping_kind,confidence)
                   VALUES (?,?,?,'exact_canonical_match',1.0)""",
                (run_id, record_id, canonical_id),
            )
            for fact_id in fact_ids:
                db.execute(
                    "INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1.0)",
                    (fact_id, record_id),
                )
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {
        "release_id": release["id"],
        "release_sha256": actual_sha,
        "selection": {"levels": list(levels)},
        "coverage_by_level": {
            level: sum(row.cefr_level == level for row in rows)
            for level in levels
        },
        "source_rows_selected": len(rows),
        "canonical_objects_mapped": len(resolved),
        "facts_evidenced": len(resolved) * 3,
        "unmapped_rows": 0,
        "duplicate_source_identities": 0,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

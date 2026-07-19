#!/usr/bin/env python3
"""Import exact POS French source definitions for unresolved A1–B2 words.

The adapter intentionally imports only exact surface and POS matches.  It does
not turn a source noun into an adjective, or a conjugated form into a lexical
lemma, merely to increase coverage.  Those cases remain explicit for later
review or a better-aligned source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import unicodedata
import uuid
from collections import Counter
from pathlib import Path

import pandas as pd

from canonical_identity import NAMESPACE, canonical_uuid


SOURCE_POS_TO_GRAPH_POS = {
    "N": "NOM",
    "V": "VER",
    "Adj": "ADJ",
    "Adv": "ADV",
    "pronom": "PRO",
    "pronom-pers": "PRO",
    "pronom-pos": "PRO",
    "pronom-int": "PRO",
    "pronom-rel": "PRO",
    "prép": "PRP",
    "conj": "KON",
    "conj-coord": "KON",
    "interj": "INT",
    "art-part": "DET",
}


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_levels(manifest: dict) -> tuple[str, ...]:
    levels = tuple(manifest["import"]["selection"]["levels"])
    if not levels or any(level not in {"A1", "A2", "B1", "B2", "C1", "C2"} for level in levels):
        raise ValueError(f"Invalid CEFR selection: {levels!r}")
    return levels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    if sha256(args.source) != manifest["release"]["sha256"]:
        raise ValueError("French dictionary source SHA-256 mismatch")

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")
    levels = selected_levels(manifest)
    release = manifest["release"]
    release_id = release["id"]
    import_run_id = f"import:{release_id}:{'-'.join(level.casefold() for level in levels)}-definitions"
    catalog = manifest["catalog"]
    database.execute(
        """INSERT OR IGNORE INTO sources(id, name, url, license, citation)
           VALUES (?, ?, ?, ?, ?)""",
        (catalog["id"], catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
    )
    database.execute(
        """INSERT OR IGNORE INTO source_catalogs
           (id, name, homepage_url, license, attribution_text)
           VALUES (?, ?, ?, ?, ?)""",
        (catalog["id"], catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
    )
    database.execute(
        """INSERT OR IGNORE INTO source_releases
           (id, catalog_id, release_label, artifact_uri, sha256, scope_description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (release_id, catalog["id"], release["label"], release["artifact_uri"], release["sha256"], release["scope"]),
    )
    database.execute(
        """INSERT OR IGNORE INTO import_runs
           (id, release_id, importer_name, importer_version, status, completed_at)
           VALUES (?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)""",
        (import_run_id, release_id, manifest["import"]["adapter"], manifest["import"]["adapter_version"]),
    )

    placeholders = ",".join("?" for _ in levels)
    scoped_words = {
        (normalize(row["canonical_form"]), row["part_of_speech"]): dict(row)
        for row in database.execute(
            f"""SELECT word.id, word.canonical_form, word.part_of_speech, word.cefr_level,
                       canonical.canonical_id
                FROM language_objects AS word
                JOIN canonical_objects AS canonical ON canonical.language_object_id = word.id
                WHERE word.type_code = 'word' AND word.cefr_level IN ({placeholders})""",
            levels,
        )
    }
    unresolved_words = {
        key: owner
        for key, owner in scoped_words.items()
        if not database.execute(
            "SELECT 1 FROM lexical_senses WHERE owner_canonical_id = ? LIMIT 1",
            (owner["canonical_id"],),
        ).fetchone()
    }
    orthographic_reconciliations = {
        (normalize(item["source_form"]), item["source_part_of_speech"]): item
        for item in manifest["import"].get("orthographic_reconciliations", [])
    }

    frame = pd.read_parquet(args.source, columns=["forme", "pos", "gloss", "def_index", "sub_index"])
    frame = frame[frame["gloss"].notna()].copy()
    frame["target_pos"] = frame["pos"].map(SOURCE_POS_TO_GRAPH_POS)
    frame = frame[frame["target_pos"].notna()]
    frame["normalized_form"] = frame["forme"].map(normalize)
    frame = frame.sort_values(["normalized_form", "target_pos", "def_index", "sub_index"], na_position="last")

    matched_keys: set[tuple[str, str]] = set()
    imported_senses: set[str] = set()
    imported_definition_facts: set[str] = set()
    matched_source_records: set[str] = set()
    source_categories: Counter[str] = Counter()
    mapping_kinds: Counter[str] = Counter()

    database.commit()
    database.execute("DELETE FROM import_exclusions WHERE import_run_id = ?", (import_run_id,))
    database.commit()
    database.execute("BEGIN")
    try:
        for row in frame.itertuples(index=False):
            key = (row.normalized_form, row.target_pos)
            owner = unresolved_words.get(key)
            mapping_kind = "exact_pos_match"
            mapping_confidence = 1.0
            if owner is None:
                reconciliation = orthographic_reconciliations.get((row.normalized_form, row.pos))
                if reconciliation:
                    owner = scoped_words.get(
                        (normalize(reconciliation["target_word"]), reconciliation["target_part_of_speech"])
                    )
                    mapping_kind = "orthographic_reconciliation"
                    mapping_confidence = float(reconciliation.get("confidence", 1.0))
            if not owner:
                continue
            gloss = str(row.gloss).strip()
            if not gloss:
                continue
            source_key = "|".join(
                [str(row.forme), str(row.pos), str(row.def_index), "" if pd.isna(row.sub_index) else str(row.sub_index)]
            )
            source_payload = {
                "forme": row.forme,
                "pos": row.pos,
                "definition_index": int(row.def_index),
                "sub_index": None if pd.isna(row.sub_index) else int(row.sub_index),
                "gloss": gloss,
            }
            record_id = stable_id("source-record", f"{release_id}|{source_key}")
            database.execute(
                """INSERT OR IGNORE INTO source_records
                   (id, release_id, external_key, record_kind, content_hash)
                   VALUES (?, ?, ?, 'lexical_sense', ?)""",
                (record_id, release_id, source_key, hashlib.sha256(json.dumps(source_payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()),
            )
            semantic_key = f"{row.target_pos}|fr|{normalize(gloss)}"
            identity_key = f"fr|lexical_sense|owner={owner['canonical_id']}|semantic={semantic_key}"
            sense_canonical_id = canonical_uuid(identity_key)
            sense_hash = hashlib.sha256(identity_key.encode()).hexdigest()[:16]
            sense_object_id = f"fr:sense:{owner['id'].removeprefix('fr:')}:{sense_hash}"
            database.execute(
                """INSERT OR IGNORE INTO language_objects
                   (id, type_code, canonical_form, display_form, normalized_form,
                    cefr_level, part_of_speech, source_id, content_status, provenance)
                   VALUES (?, 'lexical_sense', ?, ?, ?, ?, ?, ?, 'metadata_ready', 'curated')""",
                (sense_object_id, owner["canonical_form"], f"{owner['canonical_form']} · French source definition", normalize(f"{owner['canonical_form']} {gloss}"), owner["cefr_level"], row.target_pos, catalog["id"]),
            )
            database.execute(
                """INSERT OR IGNORE INTO canonical_objects
                   (canonical_id, language_object_id, object_type_code, identity_key)
                   VALUES (?, ?, 'lexical_sense', ?)""",
                (sense_canonical_id, sense_object_id, identity_key),
            )
            database.execute(
                """INSERT OR IGNORE INTO lexical_senses
                   (sense_object_id, owner_canonical_id, part_of_speech, semantic_key, display_order)
                   VALUES (?, ?, ?, ?, ?)""",
                (sense_object_id, owner["canonical_id"], row.target_pos, semantic_key, int(row.def_index)),
            )
            relation_id = stable_id("relationship", f"{owner['id']}|has_sense|{sense_object_id}")
            database.execute(
                """INSERT OR IGNORE INTO relationships
                   (id, source_object_id, target_object_id, relationship_type_code, source_kind, confidence)
                   VALUES (?, ?, ?, 'has_sense', 'curated', ?)""",
                (relation_id, owner["id"], sense_object_id, mapping_confidence),
            )
            database.execute(
                """INSERT OR IGNORE INTO relationship_evidence
                   (relationship_id, source_record_id, confidence)
                   VALUES (?, ?, ?)""",
                (relation_id, record_id, mapping_confidence),
            )
            database.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (sense_object_id,))
            database.execute(
                """INSERT OR IGNORE INTO import_record_mappings
                   (import_run_id, source_record_id, canonical_id, mapping_kind, confidence)
                   VALUES (?, ?, ?, ?, ?)""",
                (import_run_id, record_id, sense_canonical_id, mapping_kind, mapping_confidence),
            )
            fact_id = stable_id("fact", f"{sense_canonical_id}|french_definition|{normalize(gloss)}")
            database.execute(
                """INSERT OR IGNORE INTO canonical_facts(id, canonical_subject_id, predicate_code)
                   VALUES (?, ?, 'french_definition')""",
                (fact_id, sense_canonical_id),
            )
            database.execute(
                """INSERT OR IGNORE INTO fact_text_values(fact_id, language_code, value_text)
                   VALUES (?, 'fr', ?)""",
                (fact_id, gloss),
            )
            database.execute(
                """INSERT OR IGNORE INTO fact_evidence(fact_id, source_record_id, evidence_role, confidence)
                   VALUES (?, ?, 'asserts', ?)""",
                (fact_id, record_id, mapping_confidence),
            )
            matched_keys.add((normalize(owner["canonical_form"]), owner["part_of_speech"]))
            imported_senses.add(sense_object_id)
            imported_definition_facts.add(fact_id)
            matched_source_records.add(record_id)
            source_categories[str(row.pos)] += 1
            mapping_kinds[mapping_kind] += 1
        database.commit()
    except Exception:
        database.rollback()
        raise

    unresolved = [
        {"lemma": data["canonical_form"], "part_of_speech": pos, "cefr_level": data["cefr_level"]}
        for (form, pos), data in sorted(scoped_words.items())
        if not database.execute(
            "SELECT 1 FROM lexical_senses WHERE owner_canonical_id = ? LIMIT 1",
            (data["canonical_id"],),
        ).fetchone()
    ]
    report = {
        "release_id": release_id,
        "selection": {"levels": list(levels)},
        "unresolved_word_pos_objects_before_import": len(unresolved_words),
        "word_pos_objects_matched_exactly": len(matched_keys),
        "word_pos_objects_without_source_definition_after_import": len(unresolved),
        "unresolved_word_pos_objects": unresolved,
        "source_sense_records_matched": len(matched_source_records),
        "lexical_sense_objects_imported": len(imported_senses),
        "french_definition_facts_imported": len(imported_definition_facts),
        "source_categories": dict(sorted(source_categories.items())),
        "mapping_kinds": dict(sorted(mapping_kinds.items())),
        "english_gloss_claimed": False,
        "automatic_pos_reconciliation_used": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "unresolved_word_pos_objects"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

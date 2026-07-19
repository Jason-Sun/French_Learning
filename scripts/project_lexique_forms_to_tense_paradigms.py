#!/usr/bin/env python3
"""Project source-backed simple forms into graph-native tense paradigms.

Lexique asserts individual form analyses.  Liens' pedagogical conjugation model
adds the derived structural path ``verb root → tense paradigm → form`` so the
browser can render those asserted forms in the appropriate learning tense.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from collections import defaultdict
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


CATALOG_ID = "liens-conjugation-form-projection"
RELEASE_ID = "liens-conjugation-form-projection-v1"
RUN_ID = "import:liens-conjugation-form-projection-v1"


def stable(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def add_relation(db: sqlite3.Connection, source: str, target: str, kind: str, source_records: list[str]) -> tuple[int, int]:
    proposed_id = stable("relationship", f"{source}|{kind}|{target}")
    db.execute(
        """INSERT OR IGNORE INTO relationships
           (id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence)
           VALUES (?,?,?,?, 'curated',1.0)""",
        (proposed_id, source, target, kind),
    )
    created = db.execute("SELECT changes()").fetchone()[0]
    relation_id = db.execute(
        "SELECT id FROM relationships WHERE source_object_id=? AND target_object_id=? AND relationship_type_code=?",
        (source, target, kind),
    ).fetchone()[0]
    evidence = 0
    for record in source_records:
        db.execute(
            "INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,evidence_role,confidence) VALUES (?,?,'derived_from_asserted_form',1.0)",
            (relation_id, record),
        )
        evidence += db.execute("SELECT changes()").fetchone()[0]
    return created, evidence


def ensure_root_paradigm(
    db: sqlite3.Connection,
    lemma_id: str,
    lemma_display: str,
    lemma_canonical_id: str,
    source_records: list[str],
) -> tuple[str, int, int]:
    """Return the verb's graph-native root paradigm, creating it if needed.

    Lexique asserts individual form analyses rather than a learner-facing root
    paradigm.  The root is therefore a transparent Liens derivation, created
    only when source-backed forms prove that the verb has a conjugation path.
    """
    existing = db.execute(
        """SELECT target_object_id FROM relationships
           WHERE source_object_id=? AND relationship_type_code='belongs_to_conjugation'
           ORDER BY target_object_id LIMIT 1""",
        (lemma_id,),
    ).fetchone()
    if existing:
        return existing[0], 0, 0

    root_id = f"fr:paradigm:{lemma_id}"
    identity_key = f"fr|conjugation_paradigm|owner={lemma_canonical_id}|scope=root"
    db.execute(
        """INSERT OR IGNORE INTO language_objects
           (id,type_code,canonical_form,display_form,normalized_form,part_of_speech,
            source_id,content_status,provenance)
           VALUES (?,?,?,?,?,'VER',?,'metadata_ready','curated')""",
        (root_id, "conjugation_paradigm", lemma_display, f"{lemma_display} conjugation", lemma_display.casefold(), CATALOG_ID),
    )
    db.execute(
        """INSERT OR IGNORE INTO canonical_objects
           (canonical_id,language_object_id,object_type_code,identity_key)
           VALUES (?,?, 'conjugation_paradigm', ?)""",
        (canonical_uuid(identity_key), root_id, identity_key),
    )
    db.execute(
        """INSERT OR IGNORE INTO object_attributes(object_id,key,value_json)
           VALUES (?, 'conjugation_root', ?)""",
        (root_id, json.dumps({"owner_object_id": lemma_id, "version": 1})),
    )
    created, evidence = add_relation(db, lemma_id, root_id, "belongs_to_conjugation", source_records)
    return root_id, created, evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute(
        "INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)",
        (CATALOG_ID, "Liens conjugation form projection", "app://liens/conjugation-form-projection", "Internal reproducible derivation", "Tense-paradigm structure is derived from source-backed form analyses."),
    )
    db.execute(
        "INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text,replacement_policy) VALUES (?,?,?,?,?,?)",
        (CATALOG_ID, "Liens conjugation form projection", "app://liens/conjugation-form-projection", "Internal reproducible derivation", "Tense-paradigm edges are deterministically projected from source-backed form analyses; this is not a lexical source.", "replaceable"),
    )
    db.execute(
        "INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,sha256,scope_description) VALUES (?,?,?,?,?,?)",
        (RELEASE_ID, CATALOG_ID, "v1", "scripts/project_lexique_forms_to_tense_paradigms.py", source_hash, "Projects existing source-backed simple forms into Liens tense paradigms."),
    )
    db.execute(
        "INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,configuration_hash,status,completed_at) VALUES (?,?,?,?,?,'completed',CURRENT_TIMESTAMP)",
        (RUN_ID, RELEASE_ID, "project_lexique_forms_to_tense_paradigms.py", "1", source_hash),
    )
    tense_rows = list(db.execute("SELECT object_id,mood,tense,display_order,formation FROM conjugation_tense_metadata"))
    tense_by_feature = {(row["mood"], row["tense"]): row for row in tense_rows}
    forms = list(db.execute(
        """SELECT form.id AS form_id, form.display_form AS form_display, form_canonical.canonical_id AS form_canonical_id,
                  lemma.id AS lemma_id, lemma.display_form AS lemma_display, lemma_canonical.canonical_id AS lemma_canonical_id,
                  root.target_object_id AS root_paradigm_id, features.mood, features.tense
           FROM language_objects AS form
           JOIN form_features AS features ON features.object_id=form.id
           JOIN relationships AS lemma_link ON lemma_link.source_object_id=form.id
             AND lemma_link.relationship_type_code='inflected_form_of'
           JOIN language_objects AS lemma ON lemma.id=lemma_link.target_object_id
           LEFT JOIN relationships AS root ON root.source_object_id=lemma.id
             AND root.relationship_type_code='belongs_to_conjugation'
           JOIN canonical_objects AS form_canonical ON form_canonical.language_object_id=form.id
           JOIN canonical_objects AS lemma_canonical ON lemma_canonical.language_object_id=lemma.id
           WHERE form.type_code='inflected_form' AND form.source_id='lexique383'
           ORDER BY form.id"""
    ))
    # Avoid a source-record query for every form. A production release may
    # project tens of thousands of analyses, so provenance is loaded once and
    # reused without weakening its relationship-level evidence.
    source_records_by_canonical: dict[str, list[str]] = defaultdict(list)
    for row in db.execute(
        """SELECT DISTINCT mapping.canonical_id, mapping.source_record_id
           FROM import_record_mappings AS mapping
           JOIN source_records AS record ON record.id=mapping.source_record_id
           JOIN source_releases AS release ON release.id=record.release_id
           WHERE release.catalog_id<>?""",
        (CATALOG_ID,),
    ):
        source_records_by_canonical[row["canonical_id"]].append(row["source_record_id"])
    db.commit()

    created_roots = created_paradigms = root_edges = tense_edges = form_edges = evidence_edges = skipped = 0
    db.execute("BEGIN")
    try:
        for form in forms:
            tense = tense_by_feature.get((form["mood"], form["tense"]))
            if not tense:
                skipped += 1
                continue
            source_records = source_records_by_canonical.get(form["form_canonical_id"], [])
            root_paradigm_id = form["root_paradigm_id"]
            if not root_paradigm_id:
                root_paradigm_id, created, evidence = ensure_root_paradigm(
                    db,
                    form["lemma_id"],
                    form["lemma_display"],
                    form["lemma_canonical_id"],
                    source_records,
                )
                if created:
                    created_roots += 1
                root_edges += created
                evidence_edges += evidence
            tense_object_id = tense["object_id"]
            tense_paradigm_id = f"fr:paradigm:{form['lemma_id']}:{form['mood']}:{form['tense']}"
            existing = db.execute("SELECT 1 FROM language_objects WHERE id=?", (tense_paradigm_id,)).fetchone()
            if not existing:
                canonical_form = f"{form['lemma_display']} {form['mood']} {form['tense']}"
                identity_key = f"fr|conjugation_paradigm|owner={form['lemma_canonical_id']}|mood={form['mood']}|tense={form['tense']}"
                db.execute(
                    """INSERT INTO language_objects
                       (id,type_code,canonical_form,display_form,normalized_form,part_of_speech,source_id,content_status,provenance)
                       VALUES (?,?,?,?,?,'VER',?,'metadata_ready','curated')""",
                    (tense_paradigm_id, "conjugation_paradigm", canonical_form, db.execute("SELECT display_form FROM language_objects WHERE id=?", (tense_object_id,)).fetchone()[0], canonical_form.casefold(), CATALOG_ID),
                )
                db.execute(
                    "INSERT INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)",
                    (canonical_uuid(identity_key), tense_paradigm_id, "conjugation_paradigm", identity_key),
                )
                db.execute(
                    "INSERT INTO object_attributes(object_id,key,value_json) VALUES (?,?,?)",
                    (tense_paradigm_id, "conjugation_features", json.dumps({"mood": form["mood"], "tense": form["tense"], "label": db.execute("SELECT display_form FROM language_objects WHERE id=?", (tense_object_id,)).fetchone()[0], "display_order": tense["display_order"], "formation": tense["formation"], "tense_object_id": tense_object_id, "version": 1})),
                )
                created_paradigms += 1
            created, evidence = add_relation(db, root_paradigm_id, tense_paradigm_id, "contains", source_records)
            root_edges += created; evidence_edges += evidence
            created, evidence = add_relation(db, tense_paradigm_id, tense_object_id, "realizes_tense", source_records)
            tense_edges += created; evidence_edges += evidence
            created, evidence = add_relation(db, form["form_id"], tense_paradigm_id, "member_of_paradigm", source_records)
            form_edges += created; evidence_edges += evidence
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {
        "forms_examined": len(forms),
        "forms_without_catalogued_tense": skipped,
        "root_paradigms_created": created_roots,
        "tense_paradigms_created": created_paradigms,
        "root_contains_edges_created": root_edges,
        "realizes_tense_edges_created": tense_edges,
        "member_of_paradigm_edges_created": form_edges,
        "relationship_evidence_edges_created": evidence_edges,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

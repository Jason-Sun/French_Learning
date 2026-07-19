#!/usr/bin/env python3
"""Derive evidence-backed French verb-group facts from the local graph.

The policy is deliberately narrow: it does not claim a source directly asserts a
group.  Instead it records a deterministic derivation from the canonical lemma
and, for -ir verbs, the imported Lexique present participle.  The browser reads
the resulting canonical ``verb_group`` fact; ``verb_metadata`` is left as a
legacy compatibility adapter for auxiliary and stem data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

from canonical_identity import NAMESPACE


CATALOG_ID = "liens-verb-group-derivation"
RELEASE_ID = "liens-verb-group-derivation-v1"
RUN_ID = "import:liens-verb-group-derivation-v1"


def stable(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_records_for(db: sqlite3.Connection, canonical_id: str) -> list[str]:
    return [row[0] for row in db.execute(
        """SELECT DISTINCT mapping.source_record_id
           FROM import_record_mappings AS mapping
           JOIN source_records AS record ON record.id=mapping.source_record_id
           JOIN source_releases AS release ON release.id=record.release_id
           WHERE mapping.canonical_id=? AND release.catalog_id<>?""",
        (canonical_id, CATALOG_ID),
    )]


def classify(lemma: str, present_participles: list[str], exceptions: set[str]) -> tuple[str | None, str]:
    if lemma.endswith("er") and lemma not in exceptions:
        return "first_group", "infinitive_er"
    if lemma.endswith("ir"):
        if not present_participles:
            return None, "missing_present_participle"
        if any(form.endswith("issant") for form in present_participles):
            return "second_group", "present_participle_issant"
        return "third_group", "present_participle_not_issant"
    return "third_group", "non_er_non_ir_infinitive"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    policy_hash = digest(args.policy)
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    db.execute(
        "INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)",
        ("verb_group", "code", "French verb group", "Deterministically derived from canonical lemma spelling and available morphology under a versioned Liens policy."),
    )
    db.execute(
        "INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text,replacement_policy) VALUES (?,?,?,?,?,?)",
        (CATALOG_ID, "Liens deterministic grammar derivations", "app://liens/verb-group-policy", "Internal reproducible derivation policy", "Verb groups are derived from cited lexical and morphology records; this policy is not a lexical source.", "replaceable"),
    )
    db.execute(
        "INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,sha256,scope_description) VALUES (?,?,?,?,?,?)",
        (RELEASE_ID, CATALOG_ID, policy["policy_id"], str(args.policy), policy_hash, "French verb-group derivation policy and its recorded inputs."),
    )
    db.execute(
        "INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,configuration_hash,status,completed_at) VALUES (?,?,?,?,?,'completed',CURRENT_TIMESTAMP)",
        (RUN_ID, RELEASE_ID, "derive_verb_groups.py", "1", policy_hash),
    )

    exceptions = set(policy.get("third_group_exceptions", []))
    verbs = list(db.execute(
        """SELECT word.id AS object_id, word.normalized_form, canonical.canonical_id
           FROM language_objects AS word
           JOIN canonical_objects AS canonical ON canonical.language_object_id=word.id
           WHERE word.type_code='word' AND word.part_of_speech IN ('VER','V')
           ORDER BY word.id"""
    ))
    classified = unresolved = evidence_links = 0
    counts: dict[str, int] = {"first_group": 0, "second_group": 0, "third_group": 0}

    # Persist the import infrastructure before the repeatable per-verb unit.
    db.commit()
    db.execute("BEGIN")
    try:
        # A prior pre-release run could have treated this derivation record as
        # lexical evidence. Keep only the explicit `derived_by` policy link.
        db.execute(
            """DELETE FROM fact_evidence
               WHERE evidence_role='derived_from_lemma'
                 AND source_record_id IN (
                   SELECT record.id FROM source_records AS record
                   JOIN source_releases AS release ON release.id=record.release_id
                   WHERE release.catalog_id=?
                 )""",
            (CATALOG_ID,),
        )
        db.execute(
            """DELETE FROM fact_evidence
               WHERE evidence_role='derived_from_present_participle'
                 AND fact_id IN (
                   SELECT fact.id FROM canonical_facts AS fact
                   JOIN canonical_objects AS canonical ON canonical.canonical_id=fact.canonical_subject_id
                   JOIN language_objects AS word ON word.id=canonical.language_object_id
                   WHERE fact.predicate_code='verb_group' AND word.normalized_form NOT LIKE '%ir'
                 )"""
        )
        for verb in verbs:
            participle_rows = list(db.execute(
                """SELECT form.display_form, form_canonical.canonical_id
                   FROM relationships AS edge
                   JOIN language_objects AS form ON form.id=edge.source_object_id
                   JOIN form_features AS features ON features.object_id=form.id
                   JOIN canonical_objects AS form_canonical ON form_canonical.language_object_id=form.id
                   WHERE edge.target_object_id=? AND edge.relationship_type_code='inflected_form_of'
                     AND features.mood='participle' AND features.tense='present'
                   ORDER BY form.id""",
                (verb["object_id"],),
            ))
            participles = [row["display_form"].casefold() for row in participle_rows]
            group, rule = classify(verb["normalized_form"], participles, exceptions)
            derivation_key = f"{verb['canonical_id']}|{rule}|{group or 'unresolved'}|{'|'.join(participles)}"
            record_id = stable("source-record", f"{RELEASE_ID}|{derivation_key}")
            db.execute(
                "INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",
                (record_id, RELEASE_ID, verb["canonical_id"], "verb_group_derivation", hashlib.sha256(derivation_key.encode()).hexdigest()),
            )
            # A prior version of the same policy may have used a different
            # deterministic record ID for the release/key uniqueness tuple.
            # Resolve the stored record before attaching evidence so a repeat
            # build never points at an ignored, non-existent proposed ID.
            record_id = db.execute(
                """SELECT id FROM source_records
                   WHERE release_id=? AND external_key=? AND record_kind='verb_group_derivation'""",
                (RELEASE_ID, verb["canonical_id"]),
            ).fetchone()[0]
            if not group:
                db.execute(
                    "INSERT OR IGNORE INTO import_exclusions(import_run_id,source_record_id,reason_code,explanation) VALUES (?,?,?,?)",
                    (RUN_ID, record_id, "insufficient_morphology", "An -ir infinitive needs a source-backed present participle before it can be assigned to group two or three."),
                )
                unresolved += 1
                continue

            fact_id = stable("fact", f"{verb['canonical_id']}|verb_group|{group}")
            db.execute("INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)", (fact_id, verb["canonical_id"], "verb_group"))
            db.execute("INSERT OR IGNORE INTO fact_code_values(fact_id,value_code) VALUES (?,?)", (fact_id, group))
            db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'derived_by',1.0)", (fact_id, record_id))
            for source_record in source_records_for(db, verb["canonical_id"]):
                db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'derived_from_lemma',1.0)", (fact_id, source_record))
                evidence_links += db.execute("SELECT changes()").fetchone()[0]
            if rule in {"present_participle_issant", "present_participle_not_issant"}:
                for participle in participle_rows:
                    for source_record in source_records_for(db, participle["canonical_id"]):
                        db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'derived_from_present_participle',1.0)", (fact_id, source_record))
                        evidence_links += db.execute("SELECT changes()").fetchone()[0]
            db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'verb_group_derivation',1.0)", (RUN_ID, record_id, verb["canonical_id"]))
            classified += 1
            counts[group] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {
        "policy_id": policy["policy_id"],
        "policy_sha256": policy_hash,
        "verb_lemmas_examined": len(verbs),
        "classified": classified,
        "unresolved": unresolved,
        "by_group": counts,
        "fact_evidence_links_added": evidence_links,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

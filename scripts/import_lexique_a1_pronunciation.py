#!/usr/bin/env python3
"""Import Lexique pronunciation representations for the A1 graph.

Lexique's ``phon`` field is retained as a source-specific phonological code. It
is deliberately not converted to, or labelled as, IPA. Syllable boundaries are
stored beside that code as a separate, evidence-backed representation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


LEXIQUE_TO_GRAPH_POS = {"VER": "VER", "AUX": "VER", "NOM": "NOM", "ADJ": "ADJ"}


def normalize(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record_id(release_id: str, line_number: int) -> str:
    return stable_id("source-record", f"{release_id}|line:{line_number}|lexique_row")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    if sha256(args.source) != manifest["release"]["sha256"]:
        raise ValueError("Lexique source SHA-256 mismatch")

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")

    release_id = manifest["release"]["id"]
    import_run_id = f"import:{release_id}:a1-pronunciation"
    database.execute(
        """INSERT OR IGNORE INTO import_runs
           (id, release_id, importer_name, importer_version, status, completed_at)
           VALUES (?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)""",
        (import_run_id, release_id, "lexique383_a1_pronunciation", "1"),
    )

    a1_words = {
        (normalize(row["canonical_form"]), row["part_of_speech"]): row["id"]
        for row in database.execute(
            """SELECT lo.id, lo.canonical_form, lo.part_of_speech
               FROM language_objects lo
               WHERE lo.type_code = 'word' AND lo.cefr_level = 'A1'"""
        )
    }
    eligible_a1_word_ids = {
        object_id
        for (lemma, part_of_speech), object_id in a1_words.items()
        if part_of_speech in set(LEXIQUE_TO_GRAPH_POS.values())
    }

    eligible_rows = 0
    rows_without_phonology = 0
    rows_without_target = 0
    exclusions_by_reason: dict[str, int] = {}
    owner_ids: set[str] = set()
    database.commit()
    database.execute("DELETE FROM import_exclusions WHERE import_run_id = ?", (import_run_id,))
    database.commit()
    database.execute("BEGIN")

    try:
        with args.source.open(encoding="utf8") as source:
            for line_number, row in enumerate(csv.DictReader(source, delimiter="\t"), start=2):
                part_of_speech = LEXIQUE_TO_GRAPH_POS.get(row["cgram"])
                key = (normalize(row["lemme"]), part_of_speech)
                if part_of_speech is None or key not in a1_words:
                    continue

                eligible_rows += 1
                if not row["phon"]:
                    rows_without_phonology += 1
                    continue

                record_id = source_record_id(release_id, line_number)
                # One immutable source row may support morphology and pronunciation.
                # Earlier morphology commits used this same identity with a narrower
                # record kind; normalize that label without changing the row identity.
                database.execute(
                    """INSERT OR IGNORE INTO source_records
                       (id, release_id, external_key, record_kind, content_hash)
                       VALUES (?, ?, ?, 'lexique_row', ?)""",
                    (
                        record_id,
                        release_id,
                        f"line:{line_number}",
                        hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest(),
                    ),
                )
                database.execute(
                    """UPDATE source_records SET record_kind = 'lexique_row'
                       WHERE id = ? AND record_kind IN ('morphology_row', 'phonology_row')""",
                    (record_id,),
                )

                mapped_owners = database.execute(
                    """SELECT co.language_object_id
                       FROM import_record_mappings mapping
                       JOIN canonical_objects co ON co.canonical_id = mapping.canonical_id
                       WHERE mapping.source_record_id = ?""",
                    (record_id,),
                ).fetchall()
                owners = [mapped["language_object_id"] for mapped in mapped_owners]
                if not owners and normalize(row["ortho"]) == normalize(row["lemme"]):
                    owners = [a1_words[key]]
                if not owners:
                    rows_without_target += 1
                    existing_surface = database.execute(
                        """SELECT id FROM language_objects
                           WHERE type_code = 'word'
                             AND normalized_form = ?
                             AND part_of_speech = ?""",
                        (normalize(row["ortho"]), part_of_speech),
                    ).fetchone()
                    if existing_surface:
                        exclusion_reason = "conflicting_surface_identity"
                        explanation = (
                            "The Lexique surface is already a different lexical word; "
                            "the source lemma link conflicts with that identity."
                        )
                    elif row["infover"] == "inf;":
                        exclusion_reason = "unmodeled_spelling_variant"
                        explanation = (
                            "Lexique supplies an infinitive spelling variant, but the "
                            "current morphology model has no verified variant relation."
                        )
                    else:
                        exclusion_reason = "unmodeled_form_features"
                        explanation = (
                            "Lexique supplies a non-lemma surface without the structured "
                            "features needed to create a canonical form object."
                        )
                    database.execute(
                        """INSERT OR IGNORE INTO import_exclusions
                           (import_run_id, source_record_id, reason_code, explanation)
                           VALUES (?, ?, ?, ?)""",
                        (import_run_id, record_id, exclusion_reason, explanation),
                    )
                    exclusions_by_reason[exclusion_reason] = (
                        exclusions_by_reason.get(exclusion_reason, 0) + 1
                    )
                    continue

                for owner_id in set(owners):
                    pronunciation_object_id = f"fr:pronunciation:lexique383:{owner_id.removeprefix('fr:')}"
                    identity_key = f"fr|pronunciation||{owner_id}|lexique383"
                    database.execute(
                        """INSERT OR IGNORE INTO language_objects
                           (id, type_code, canonical_form, display_form, normalized_form,
                            source_id, content_status, provenance)
                           VALUES (?, 'pronunciation', ?, 'Pronunciation', ?,
                                   'lexique383', 'metadata_ready', 'curated')""",
                        (
                            pronunciation_object_id,
                            f"{row['ortho']} pronunciation",
                            f"{normalize(row['ortho'])} pronunciation",
                        ),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO canonical_objects
                           (canonical_id, language_object_id, object_type_code, identity_key)
                           VALUES (?, ?, 'pronunciation', ?)""",
                        (canonical_uuid(identity_key), pronunciation_object_id, identity_key),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO relationships
                           (id, source_object_id, target_object_id, relationship_type_code,
                            source_kind, confidence)
                           VALUES (?, ?, ?, 'has_pronunciation', 'curated', 1)""",
                        (
                            stable_id(
                                "relationship",
                                f"{owner_id}|has_pronunciation|{pronunciation_object_id}",
                            ),
                            owner_id,
                            pronunciation_object_id,
                        ),
                    )
                    pronunciation_relationship = database.execute(
                        """SELECT id FROM relationships
                           WHERE source_object_id = ? AND target_object_id = ?
                             AND relationship_type_code = 'has_pronunciation'""",
                        (owner_id, pronunciation_object_id),
                    ).fetchone()["id"]
                    database.execute(
                        """INSERT OR IGNORE INTO relationship_evidence
                           (relationship_id, source_record_id, confidence)
                           VALUES (?, ?, 1)""",
                        (pronunciation_relationship, record_id),
                    )
                    owner_ids.add(owner_id)

                    representations = (
                        ("phonological_code", "lexique383", row["phon"], None),
                        (
                            "syllabification",
                            "lexique383",
                            None,
                            json.dumps(row["syll"].split("-"), ensure_ascii=False),
                        ),
                    )
                    for kind, system, value_text, value_json in representations:
                        representation_id = stable_id(
                            "pronunciation-representation",
                            f"{pronunciation_object_id}|{kind}|{system}|{value_text or value_json}",
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO pronunciation_representations
                               (id, pronunciation_object_id, representation_kind,
                                transcription_system, value_text, value_json, confidence)
                               VALUES (?, ?, ?, ?, ?, ?, 1)""",
                            (
                                representation_id,
                                pronunciation_object_id,
                                kind,
                                system,
                                value_text,
                                value_json,
                            ),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO pronunciation_representation_evidence
                               (representation_id, source_record_id, confidence)
                               VALUES (?, ?, 1)""",
                            (representation_id, record_id),
                        )
        database.commit()
    except Exception:
        database.rollback()
        raise

    representation_counts = {
        row["representation_kind"]: row["count"]
        for row in database.execute(
            """SELECT representation_kind, COUNT(*) AS count
               FROM pronunciation_representations
               WHERE transcription_system = 'lexique383'
               GROUP BY representation_kind"""
        )
    }
    report = {
        "release_id": release_id,
        "representation_system": "lexique383",
        "ipa_claimed": False,
        "eligible_source_rows": eligible_rows,
        "source_rows_without_phonology": rows_without_phonology,
        "source_rows_without_canonical_target": rows_without_target,
        "source_rows_mapped_to_targets": eligible_rows - rows_without_phonology - rows_without_target,
        "exclusions_by_reason": exclusions_by_reason,
        "language_objects_covered": len(owner_ids),
        "eligible_a1_lemma_objects": len(eligible_a1_word_ids),
        "representation_values_total": sum(representation_counts.values()),
        "representation_counts": representation_counts,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

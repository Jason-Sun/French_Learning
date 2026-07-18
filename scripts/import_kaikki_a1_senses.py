#!/usr/bin/env python3
"""Import source-backed English lexical senses for the FLELex A1 inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import unicodedata
import uuid
from collections import Counter
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


KAikki_TO_GRAPH_POS = {
    "noun": "NOM",
    "verb": "VER",
    "adj": "ADJ",
    "adv": "ADV",
    "pron": "PRO",
    "prep": "PRP",
    "conj": "KON",
    "intj": "INT",
    "article": "DET:ART",
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


def target_pos(entry: dict, words: dict[tuple[str, str], tuple[str, str]], reconciliations: dict[tuple[str, str], str]) -> tuple[str | None, str]:
    source_pos = entry.get("pos")
    if source_pos != "det":
        reconciled = reconciliations.get((normalize(entry["word"]), source_pos))
        if reconciled and (normalize(entry["word"]), reconciled) in words:
            return reconciled, "reviewed_pos_reconciliation"
        exact = KAikki_TO_GRAPH_POS.get(source_pos)
        if exact and (normalize(entry["word"]), exact) in words:
            return exact, "exact_pos_match"
        return exact, "exact_pos_match"

    candidates = [
        part_of_speech
        for part_of_speech in ("DET:ART", "DET:POS")
        if (normalize(entry["word"]), part_of_speech) in words
    ]
    if len(candidates) == 1:
        return candidates[0], "exact_pos_match"
    reconciled = reconciliations.get((normalize(entry["word"]), source_pos))
    if reconciled and (normalize(entry["word"]), reconciled) in words:
        return reconciled, "reviewed_pos_reconciliation"
    return None, "exact_pos_match"


def glosses_for(sense: dict) -> list[str]:
    return [gloss.strip() for gloss in sense.get("glosses", []) if isinstance(gloss, str) and gloss.strip()]


def semantic_key(part_of_speech: str, glosses: list[str]) -> str:
    # The source sense ID is recorded as evidence mapping, not made canonical
    # identity. A normalized semantic signature gives the first import a durable
    # reconciliation key that a future source adapter can match or review.
    return f"{part_of_speech}|" + "\u241f".join(normalize(gloss) for gloss in glosses)


def selected_levels(manifest: dict) -> tuple[str, ...]:
    selection = manifest["import"].get("selection", {})
    raw_levels = selection.get("levels") or [selection.get("level", "A1")]
    levels = tuple(sorted({str(level).strip() for level in raw_levels if str(level).strip()}))
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
        raise ValueError("Kaikki source SHA-256 mismatch")

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")
    catalog = manifest["catalog"]
    release = manifest["release"]
    release_id = release["id"]
    levels = selected_levels(manifest)
    selection_id = "-".join(level.casefold() for level in levels)
    import_run_id = f"import:{release_id}:{selection_id}-senses"

    database.execute(
        """INSERT OR IGNORE INTO sources(id, name, url, license, citation)
           VALUES ('kaikki-enwiktionary', ?, ?, ?, ?)""",
        (catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
    )
    database.execute(
        """INSERT OR IGNORE INTO source_catalogs
           (id, name, homepage_url, license, attribution_text)
           VALUES (?, ?, ?, ?, ?)""",
        (
            catalog["id"],
            catalog["name"],
            catalog["homepage_url"],
            catalog["license"],
            catalog["attribution_text"],
        ),
    )
    database.execute(
        """INSERT OR IGNORE INTO source_releases
           (id, catalog_id, release_label, artifact_uri, sha256, scope_description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            release_id,
            catalog["id"],
            release["label"],
            release["artifact_uri"],
            release["sha256"],
            release["scope"],
        ),
    )
    database.execute(
        """INSERT OR IGNORE INTO import_runs
           (id, release_id, importer_name, importer_version, status, completed_at)
           VALUES (?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)""",
        (import_run_id, release_id, manifest["import"]["adapter"], manifest["import"]["adapter_version"]),
    )

    placeholders = ",".join("?" for _ in levels)
    words = {
        (normalize(row["canonical_form"]), row["part_of_speech"]): (
            row["id"],
            row["canonical_id"],
            row["canonical_form"],
            row["cefr_level"],
        )
        for row in database.execute(
            f"""SELECT object.id, object.canonical_form, object.part_of_speech,
                      object.cefr_level, canonical.canonical_id
               FROM language_objects object
               JOIN canonical_objects canonical ON canonical.language_object_id = object.id
               WHERE object.type_code = 'word' AND object.cefr_level IN ({placeholders})""",
            levels,
        )
    }
    reconciliations = {
        (normalize(item["word"]), item["source_part_of_speech"]): item["target_part_of_speech"]
        for item in manifest["import"].get("pos_reconciliations", [])
    }
    matched_word_keys: set[tuple[str, str]] = set()
    imported_sense_ids: set[str] = set()
    imported_gloss_fact_ids: set[str] = set()
    source_entries = 0
    source_senses_without_gloss = 0
    source_categories: Counter[str] = Counter()
    database.commit()
    database.execute("DELETE FROM import_exclusions WHERE import_run_id = ?", (import_run_id,))
    database.commit()
    database.execute("BEGIN")
    try:
        with args.source.open(encoding="utf8") as source:
            for line_number, line in enumerate(source, start=1):
                entry = json.loads(line)
                if entry.get("lang_code") != "fr" or not entry.get("word"):
                    continue
                part_of_speech, mapping_kind = target_pos(entry, words, reconciliations)
                key = (normalize(entry["word"]), part_of_speech)
                if part_of_speech is None or key not in words:
                    continue

                source_entries += 1
                matched_word_keys.add(key)
                owner_id, owner_canonical_id, owner_form, cefr_level = words[key]
                source_categories[entry["pos"]] += 1
                for source_order, source_sense in enumerate(entry.get("senses", []), start=1):
                    glosses = glosses_for(source_sense)
                    source_sense_key = source_sense.get("id") or f"line:{line_number}:sense:{source_order}"
                    record_id = stable_id(
                        "source-record", f"{release_id}|sense:{source_sense_key}"
                    )
                    source_payload = {
                        "word": entry["word"],
                        "pos": entry.get("pos"),
                        "sense": source_sense,
                    }
                    database.execute(
                        """INSERT OR IGNORE INTO source_records
                           (id, release_id, external_key, record_kind, content_hash)
                           VALUES (?, ?, ?, 'lexical_sense', ?)""",
                        (
                            record_id,
                            release_id,
                            source_sense_key,
                            hashlib.sha256(
                                json.dumps(source_payload, ensure_ascii=False, sort_keys=True).encode()
                            ).hexdigest(),
                        ),
                    )
                    if not glosses:
                        source_senses_without_gloss += 1
                        database.execute(
                            """INSERT OR IGNORE INTO import_exclusions
                               (import_run_id, source_record_id, reason_code, explanation)
                               VALUES (?, ?, 'missing_english_gloss', ?)""",
                            (
                                import_run_id,
                                record_id,
                                "The matched Kaikki source sense has no extracted English gloss.",
                            ),
                        )
                        continue

                    key_text = semantic_key(part_of_speech, glosses)
                    identity_key = (
                        "fr|lexical_sense|owner="
                        f"{owner_canonical_id}|semantic={key_text}"
                    )
                    canonical_id = canonical_uuid(identity_key)
                    sense_hash = hashlib.sha256(identity_key.encode()).hexdigest()[:16]
                    sense_object_id = f"fr:sense:{owner_id.removeprefix('fr:')}:{sense_hash}"
                    database.execute(
                        """INSERT OR IGNORE INTO language_objects
                           (id, type_code, canonical_form, display_form, normalized_form,
                            cefr_level, part_of_speech, source_id, content_status, provenance)
                           VALUES (?, 'lexical_sense', ?, ?, ?, ?, ?,
                                   'kaikki-enwiktionary', 'metadata_ready', 'curated')""",
                        (
                            sense_object_id,
                            owner_form,
                            f"{owner_form} · {glosses[0]}",
                            normalize(f"{owner_form} {glosses[0]}"),
                            cefr_level,
                            part_of_speech,
                        ),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO canonical_objects
                           (canonical_id, language_object_id, object_type_code, identity_key)
                           VALUES (?, ?, 'lexical_sense', ?)""",
                        (canonical_id, sense_object_id, identity_key),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO lexical_senses
                           (sense_object_id, owner_canonical_id, part_of_speech,
                            semantic_key, display_order)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            sense_object_id,
                            owner_canonical_id,
                            part_of_speech,
                            key_text,
                            source_order,
                        ),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO relationships
                           (id, source_object_id, target_object_id, relationship_type_code,
                            source_kind, confidence)
                           VALUES (?, ?, ?, 'has_sense', 'curated', 1)""",
                        (
                            stable_id("relationship", f"{owner_id}|has_sense|{sense_object_id}"),
                            owner_id,
                            sense_object_id,
                        ),
                    )
                    has_sense_relationship = database.execute(
                        """SELECT id FROM relationships
                           WHERE source_object_id = ? AND target_object_id = ?
                             AND relationship_type_code = 'has_sense'""",
                        (owner_id, sense_object_id),
                    ).fetchone()["id"]
                    database.execute(
                        """INSERT OR IGNORE INTO relationship_evidence
                           (relationship_id, source_record_id, confidence)
                           VALUES (?, ?, 1)""",
                        (has_sense_relationship, record_id),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO learning_metadata(object_id)
                           VALUES (?)""",
                        (sense_object_id,),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO import_record_mappings
                           (import_run_id, source_record_id, canonical_id, mapping_kind, confidence)
                           VALUES (?, ?, ?, ?, 1)""",
                        (import_run_id, record_id, canonical_id, mapping_kind),
                    )
                    for gloss in glosses:
                        fact_id = stable_id("fact", f"{canonical_id}|english_gloss|{normalize(gloss)}")
                        database.execute(
                            """INSERT OR IGNORE INTO canonical_facts
                               (id, canonical_subject_id, predicate_code)
                               VALUES (?, ?, 'english_gloss')""",
                            (fact_id, canonical_id),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO fact_text_values
                               (fact_id, language_code, value_text)
                               VALUES (?, 'en', ?)""",
                            (fact_id, gloss),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO fact_evidence
                               (fact_id, source_record_id, evidence_role, confidence)
                               VALUES (?, ?, 'asserts', 1)""",
                            (fact_id, record_id),
                        )
                        imported_gloss_fact_ids.add(fact_id)
                    imported_sense_ids.add(sense_object_id)
        database.commit()
    except Exception:
        database.rollback()
        raise

    unmatched_words = [
        {"lemma": form, "part_of_speech": pos}
        for (normalized, pos), (_, _, form, _) in sorted(words.items())
        if (normalized, pos) not in matched_word_keys
    ]
    report = {
        "release_id": release_id,
        "selection": {"levels": list(levels)},
        "word_objects": len(words),
        "word_objects_matched": len(matched_word_keys),
        "word_objects_without_source_entry": len(unmatched_words),
        "unmatched_word_objects": unmatched_words,
        "matched_source_entries": source_entries,
        "lexical_sense_objects_imported": len(imported_sense_ids),
        "english_gloss_facts_imported": len(imported_gloss_fact_ids),
        "matched_senses_without_english_gloss": source_senses_without_gloss,
        "source_categories": dict(sorted(source_categories.items())),
        "ipa_claimed": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Import source-backed multi-word expressions connected to a CEFR-scoped graph."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from collections import Counter
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


WORD_TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def tokens(value: str) -> list[str]:
    return [token.replace("’", "'") for token in WORD_TOKEN.findall(value)]


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record_id(release_id: str, source_sense_id: str) -> str:
    return stable_id("source-record", f"{release_id}|phrase-sense:{source_sense_id}")


def expression_object_id(identity_key: str) -> str:
    return f"fr:expression:{hashlib.sha256(identity_key.encode()).hexdigest()[:20]}"


def selected_levels(manifest: dict) -> tuple[str, ...]:
    selection = manifest.get("import", {}).get("selection", {})
    raw = selection.get("levels") or [selection.get("level", "A1")]
    levels = tuple(sorted({str(level).strip() for level in raw if str(level).strip()}))
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
    release_id = manifest["release"]["id"]
    levels = selected_levels(manifest)
    selection_id = "-".join(level.casefold() for level in levels)
    import_run_id = f"import:{release_id}:{selection_id}-expressions"
    catalog = manifest["catalog"]
    release = manifest["release"]
    database.execute(
        """INSERT OR IGNORE INTO sources(id, name, url, license, citation)
           VALUES ('kaikki-enwiktionary', ?, ?, ?, ?)""",
        (catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
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

    # A phrase is eligible only when every lexical component resolves locally to
    # a selected-CEFR lemma or a source-backed form of such a lemma. This is a graph
    # connectivity rule, not an unsupported CEFR classification for the phrase.
    components_by_surface: dict[str, list[sqlite3.Row]] = {}
    placeholders = ",".join("?" for _ in levels)
    component_rows = database.execute(
        f"""SELECT object.id, object.normalized_form, object.type_code,
                  object.frequency_per_million
           FROM language_objects AS object
           WHERE object.type_code = 'word' AND object.cefr_level IN ({placeholders})
           UNION ALL
           SELECT form.id, form.normalized_form, form.type_code,
                  lemma.frequency_per_million
           FROM language_objects AS form
           JOIN relationships AS inflection
             ON inflection.source_object_id=form.id
            AND inflection.relationship_type_code='inflected_form_of'
           JOIN language_objects AS lemma ON lemma.id=inflection.target_object_id
           WHERE form.type_code='inflected_form' AND lemma.cefr_level IN ({placeholders})""",
        (*levels, *levels),
    )
    for row in component_rows:
        components_by_surface.setdefault(normalize(row["normalized_form"]), []).append(row)

    def resolve_component(surface: str) -> str | None:
        candidates = components_by_surface.get(normalize(surface), [])
        if not candidates:
            return None
        # Search and sentence resolution prefer a known inflected form over an
        # unrelated homographic lemma. Preserve that deterministic convention.
        ranked = sorted(
            candidates,
            key=lambda row: (
                0 if row["type_code"] == "inflected_form" else 1,
                -(row["frequency_per_million"] or 0),
                row["id"],
            ),
        )
        return ranked[0]["id"]

    stats: Counter[str] = Counter()
    imported_objects: set[str] = set()
    imported_fact_ids: set[str] = set()
    imported_component_rows: set[tuple[str, int]] = set()
    imported_relationship_ids: set[str] = set()
    database.execute("DELETE FROM import_exclusions WHERE import_run_id = ?", (import_run_id,))
    database.commit()
    database.execute("BEGIN")
    try:
        with args.source.open(encoding="utf8") as source:
            for line_number, line in enumerate(source, start=1):
                entry = json.loads(line)
                if entry.get("lang_code") != "fr" or entry.get("pos") != "phrase":
                    continue
                phrase = entry.get("word", "").strip()
                phrase_tokens = tokens(phrase)
                if len(phrase_tokens) < 2:
                    continue
                component_ids = [resolve_component(token) for token in phrase_tokens]
                for sense_order, sense in enumerate(entry.get("senses", []), start=1):
                    glosses = [gloss.strip() for gloss in sense.get("glosses", []) if isinstance(gloss, str) and gloss.strip()]
                    if not glosses:
                        continue
                    source_sense_id = sense.get("id") or f"line:{line_number}:sense:{sense_order}"
                    record_id = source_record_id(release_id, source_sense_id)
                    payload = {"word": phrase, "pos": "phrase", "sense": sense}
                    database.execute(
                        """INSERT OR IGNORE INTO source_records
                           (id, release_id, external_key, record_kind, content_hash)
                           VALUES (?, ?, ?, 'multiword_expression', ?)""",
                        (record_id, release_id, source_sense_id, hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()),
                    )
                    if any(component_id is None for component_id in component_ids):
                        database.execute(
                            """INSERT OR IGNORE INTO import_exclusions
                               (import_run_id, source_record_id, reason_code, explanation)
                               VALUES (?, ?, 'unresolved_a1_component', ?)""",
                            (import_run_id, record_id, "A Kaikki phrase component has no local selected-CEFR lemma or linked inflected-form resolution."),
                        )
                        stats["excluded_unresolved_components"] += 1
                        continue

                    identity_key = f"fr|multiword_expression|{normalize(phrase)}"
                    canonical_id = canonical_uuid(identity_key)
                    object_id = expression_object_id(identity_key)
                    database.execute(
                        """INSERT OR IGNORE INTO language_objects
                           (id, type_code, canonical_form, display_form, normalized_form,
                            source_id, content_status, provenance)
                           VALUES (?, 'expression', ?, ?, ?, 'kaikki-enwiktionary',
                                   'metadata_ready', 'curated')""",
                        (object_id, phrase, phrase, normalize(phrase)),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO canonical_objects
                           (canonical_id, language_object_id, object_type_code, identity_key)
                           VALUES (?, ?, 'expression', ?)""",
                        (canonical_id, object_id, identity_key),
                    )
                    database.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (object_id,))
                    database.execute(
                        """INSERT OR IGNORE INTO import_record_mappings
                           (import_run_id, source_record_id, canonical_id, mapping_kind, confidence)
                           VALUES (?, ?, ?, 'kaikki_phrase_expression', 1)""",
                        (import_run_id, record_id, canonical_id),
                    )
                    for gloss in glosses:
                        fact_id = stable_id("fact", f"{canonical_id}|english_translation|{normalize(gloss)}")
                        database.execute(
                            """INSERT OR IGNORE INTO canonical_facts
                               (id, canonical_subject_id, predicate_code)
                               VALUES (?, ?, 'english_translation')""",
                            (fact_id, canonical_id),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO fact_text_values
                               (fact_id, language_code, value_text) VALUES (?, 'en', ?)""",
                            (fact_id, gloss),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO fact_evidence
                               (fact_id, source_record_id, evidence_role, confidence)
                               VALUES (?, ?, 'asserts', 1)""",
                            (fact_id, record_id),
                        )
                        imported_fact_ids.add(fact_id)
                    for position, (surface, component_id) in enumerate(zip(phrase_tokens, component_ids, strict=True), start=1):
                        database.execute(
                            """INSERT OR IGNORE INTO multiword_components
                               (parent_object_id, position, component_object_id, display_surface)
                               VALUES (?, ?, ?, ?)""",
                            (object_id, position, component_id, surface),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO multiword_component_evidence
                               (parent_object_id, position, source_record_id, source_surface)
                               VALUES (?, ?, ?, ?)""",
                            (object_id, position, record_id, surface),
                        )
                        relationship_id = stable_id("relationship", f"{object_id}|contains|{component_id}")
                        database.execute(
                            """INSERT OR IGNORE INTO relationships
                               (id, source_object_id, target_object_id, relationship_type_code,
                                source_kind, confidence)
                               VALUES (?, ?, ?, 'contains', 'curated', 1)""",
                            (relationship_id, object_id, component_id),
                        )
                        database.execute(
                            """INSERT OR IGNORE INTO relationship_evidence
                               (relationship_id, source_record_id, confidence)
                               VALUES (?, ?, 1)""",
                            (relationship_id, record_id),
                        )
                        imported_component_rows.add((object_id, position))
                        imported_relationship_ids.add(relationship_id)
                    imported_objects.add(object_id)
                    stats["source_phrase_senses_matched"] += 1
        database.commit()
    except Exception:
        database.rollback()
        raise

    report = {
        "release_id": release_id,
        "selection": {"levels": list(levels)},
        "eligibility": "Kaikki phrase entry with an English gloss whose every token resolves to a selected-CEFR lemma or linked inflected form; this does not assign CEFR to the phrase.",
        "expression_objects_imported": len(imported_objects),
        "english_translation_facts_imported": len(imported_fact_ids),
        "ordered_component_rows_imported": len(imported_component_rows),
        "contains_relationships_imported": len(imported_relationship_ids),
        "matched_source_phrase_senses": stats["source_phrase_senses_matched"],
        "excluded_source_phrase_senses_unresolved_components": stats["excluded_unresolved_components"],
        "collocation_claimed": False,
        "idiom_claimed": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

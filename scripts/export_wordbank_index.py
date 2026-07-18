#!/usr/bin/env python3
"""Export SQLite as a versioned browser graph package.

The browser receives a compact lookup bootstrap for deterministic local search
and sentence analysis. Full Language Object projections live in deterministic
detail shards and are fetched only when a learner opens an object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path


DETAIL_SHARD_COUNT = 64
EXPORTED_TYPES = (
    "word",
    "lexical_sense",
    "inflected_form",
    "conjugation_realization",
    "expression",
    "idiom",
    "collocation",
    "grammar_construction",
    "grammar_topic",
    "sentence_pattern",
    "sentence",
    "learning_group",
    "conjugation_tense",
    "learning_resource",
    "pronunciation",
    "conjugation_paradigm",
)


def search_key(value: str) -> str:
    """French-insensitive lookup key; canonical text remains untouched."""
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("’", "'"))
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def compact_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def write_json(path: Path, value: object) -> dict[str, object]:
    payload = compact_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "path": path.name if path.parent.name == "browser" else str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def shard_for(object_id: str) -> str:
    return f"{int(hashlib.sha256(object_id.encode()).hexdigest()[:8], 16) % DETAIL_SHARD_COUNT:02d}"


def rows_by_object(db: sqlite3.Connection, query: str, key: str = "object_id") -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in db.execute(query):
        record = dict(row)
        grouped[record[key]].append(record)
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for manifest.json, lookup.json, and detail shards.",
    )
    args = parser.parse_args()

    db = sqlite3.connect(args.source)
    db.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in EXPORTED_TYPES)
    object_rows = list(
        db.execute(
            f"SELECT * FROM language_objects WHERE type_code IN ({placeholders}) ORDER BY id",
            EXPORTED_TYPES,
        )
    )
    object_ids = {row["id"] for row in object_rows}

    canonical_ids = {
        row["language_object_id"]: row["canonical_id"]
        for row in db.execute("SELECT language_object_id, canonical_id FROM canonical_objects")
    }
    canonical_facts: dict[str, list[dict]] = defaultdict(list)
    for row in db.execute(
        """SELECT f.canonical_subject_id, f.predicate_code, f.lifecycle,
                  cv.value_code, nv.value_number, nv.unit_code, tv.language_code,
                  tv.value_text, ov.value_canonical_id
           FROM canonical_facts AS f
           LEFT JOIN fact_code_values AS cv ON cv.fact_id = f.id
           LEFT JOIN fact_number_values AS nv ON nv.fact_id = f.id
           LEFT JOIN fact_text_values AS tv ON tv.fact_id = f.id
           LEFT JOIN fact_object_values AS ov ON ov.fact_id = f.id
           ORDER BY f.canonical_subject_id, f.predicate_code, f.id"""
    ):
        canonical_facts[row["canonical_subject_id"]].append(dict(row))

    definitions = rows_by_object(db, "SELECT * FROM object_definitions ORDER BY position")
    features = {
        row["object_id"]: dict(row)
        for row in db.execute("SELECT * FROM form_features ORDER BY object_id")
    }
    verb_metadata = {
        row["object_id"]: dict(row)
        for row in db.execute("SELECT * FROM verb_metadata ORDER BY object_id")
    }
    tense_metadata = {
        row["object_id"]: dict(row)
        for row in db.execute("SELECT * FROM conjugation_tense_metadata ORDER BY object_id")
    }
    realizations = {
        row["object_id"]: dict(row)
        for row in db.execute("SELECT * FROM conjugation_realizations ORDER BY object_id")
    }
    realization_components = rows_by_object(
        db,
        "SELECT * FROM conjugation_realization_components ORDER BY realization_id, position",
        key="realization_id",
    )
    teaching_guidance = {
        row["resource_object_id"]: dict(row)
        for row in db.execute("SELECT * FROM teaching_guidance ORDER BY resource_object_id")
    }
    attributes: dict[str, dict] = defaultdict(dict)
    for row in db.execute("SELECT object_id, key, value_json FROM object_attributes ORDER BY object_id, key"):
        attributes[row["object_id"]][row["key"]] = json.loads(row["value_json"])

    pronunciations: dict[str, list[dict]] = defaultdict(list)
    try:
        pronunciation_rows = db.execute(
            """SELECT edge.source_object_id AS owner_id, detail.*,
                      pronunciation.display_form AS pronunciation_display_form,
                      source.name AS source_name
               FROM relationships AS edge
               JOIN pronunciation_object_details AS detail
                 ON detail.object_id = edge.target_object_id
               JOIN language_objects AS pronunciation ON pronunciation.id = detail.object_id
               LEFT JOIN sources AS source ON source.id = detail.source_id
               WHERE edge.relationship_type_code = 'has_pronunciation'
                 AND detail.review_status <> 'deprecated'
               ORDER BY edge.source_object_id, detail.confidence DESC, detail.object_id"""
        )
        for row in pronunciation_rows:
            record = dict(row)
            owner_id = record.pop("owner_id")
            pronunciations[owner_id].append(record)
    except sqlite3.OperationalError:
        for row in db.execute(
            "SELECT * FROM pronunciations WHERE status <> 'deprecated' "
            "ORDER BY object_id, confidence DESC, id"
        ):
            pronunciations[row["object_id"]].append(dict(row))

    relationships: dict[str, list[dict]] = defaultdict(list)
    examples: dict[str, list[str]] = defaultdict(list)
    form_lemmas: dict[str, str] = {}
    learning_resource_targets: dict[str, str] = {}
    for row in db.execute(
        "SELECT source_object_id, target_object_id, relationship_type_code FROM relationships "
        "ORDER BY source_object_id, relationship_type_code, target_object_id"
    ):
        source_id, target_id, type_code = row
        if source_id in object_ids:
            relationships[source_id].append({"type": type_code, "target": target_id})
        if type_code == "illustrates" and target_id in object_ids:
            examples[target_id].append(source_id)
        if type_code == "inflected_form_of":
            form_lemmas[source_id] = target_id
        if type_code == "explains":
            learning_resource_targets[source_id] = target_id

    sense_examples: dict[str, list[str]] = defaultdict(list)
    try:
        for row in db.execute(
            """SELECT sense.language_object_id AS sense_object_id,
                      alignment.sentence_object_id
               FROM sentence_source_alignments AS alignment
               JOIN canonical_objects AS sense
                 ON sense.canonical_id = alignment.target_canonical_id
               ORDER BY sense.language_object_id, alignment.sentence_object_id"""
        ):
            sense_examples[row["sense_object_id"]].append(row["sentence_object_id"])
    except sqlite3.OperationalError:
        pass

    lexical_senses: dict[str, list[str]] = defaultdict(list)
    sense_owners: dict[str, str] = {}
    try:
        for row in db.execute(
            """SELECT owner.language_object_id AS owner_id, sense.sense_object_id
               FROM lexical_senses AS sense
               JOIN canonical_objects AS owner ON owner.canonical_id = sense.owner_canonical_id
               ORDER BY owner.language_object_id, sense.display_order, sense.sense_object_id"""
        ):
            lexical_senses[row["owner_id"]].append(row["sense_object_id"])
            sense_owners[row["sense_object_id"]] = row["owner_id"]
    except sqlite3.OperationalError:
        pass

    def full_object(row: sqlite3.Row) -> dict:
        item = dict(row)
        canonical_id = canonical_ids.get(row["id"])
        item["canonical_id"] = canonical_id
        item["facts"] = canonical_facts.get(canonical_id, [])
        item["search_key"] = search_key(row["normalized_form"])
        item["definitions"] = definitions.get(row["id"], [])
        item["senses"] = lexical_senses.get(row["id"], [])
        item["sense_owner_id"] = sense_owners.get(row["id"])
        item["sense_examples"] = sense_examples.get(row["id"], [])
        item["features"] = features.get(row["id"])
        item["verb_metadata"] = verb_metadata.get(row["id"])
        item["tense_metadata"] = tense_metadata.get(row["id"])
        item["realization"] = realizations.get(row["id"])
        item["realization_components"] = realization_components.get(row["id"], [])
        item["teaching_guidance"] = teaching_guidance.get(row["id"])
        item["attributes"] = attributes.get(row["id"], {})
        item["pronunciations"] = pronunciations.get(row["id"], [])
        item["relationships"] = relationships.get(row["id"], [])
        item["examples"] = examples.get(row["id"], [])
        return item

    def lookup_object(row: sqlite3.Row) -> dict:
        item = {
            key: row[key]
            for key in (
                "id",
                "type_code",
                "canonical_form",
                "display_form",
                "normalized_form",
                "cefr_level",
                "part_of_speech",
                "frequency_per_million",
                "content_status",
            )
        }
        item["search_key"] = search_key(row["normalized_form"])
        item["detail_shard"] = shard_for(row["id"])
        if row["id"] in features:
            item["features"] = features[row["id"]]
        if row["id"] in tense_metadata:
            item["tense_metadata"] = tense_metadata[row["id"]]
        if row["id"] in realizations:
            item["realization"] = realizations[row["id"]]
        if row["id"] in realization_components:
            item["realization_components"] = realization_components[row["id"]]
        if row["id"] in teaching_guidance:
            item["teaching_guidance"] = teaching_guidance[row["id"]]
        if row["id"] in attributes:
            item["attributes"] = attributes[row["id"]]
        if row["id"] in form_lemmas:
            item["lemma_id"] = form_lemmas[row["id"]]
        if row["id"] in sense_owners:
            item["sense_owner_id"] = sense_owners[row["id"]]
        if row["id"] in learning_resource_targets:
            item["explains_object_id"] = learning_resource_targets[row["id"]]
        return item

    details_by_shard: dict[str, list[dict]] = defaultdict(list)
    lookup_objects = []
    for row in object_rows:
        if row["type_code"] not in {"pronunciation", "lexical_sense", "conjugation_paradigm"}:
            lookup_objects.append(lookup_object(row))
        details_by_shard[shard_for(row["id"])].append(full_object(row))

    tense_by_features = {
        (metadata["mood"], metadata["tense"]): object_id
        for object_id, metadata in tense_metadata.items()
    }
    forms_by_lemma_and_tense: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for form_id, lemma_id in form_lemmas.items():
        feature = features.get(form_id, {})
        tense_id = tense_by_features.get((feature.get("mood"), feature.get("tense")))
        if tense_id:
            forms_by_lemma_and_tense[lemma_id][tense_id].append(form_id)

    group_tenses: dict[str, list[str]] = defaultdict(list)
    for row in db.execute(
        """SELECT source_object_id, target_object_id
           FROM relationships
           WHERE relationship_type_code = 'contains'"""
    ):
        if row["source_object_id"] in object_ids and row["target_object_id"] in tense_metadata:
            group_tenses[row["source_object_id"]].append(row["target_object_id"])
    group_records = []
    for row in object_rows:
        if row["type_code"] != "learning_group":
            continue
        group_records.append(
            {
                "id": row["id"],
                "tense_ids": group_tenses.get(row["id"], []),
                "display_order": attributes.get(row["id"], {})
                .get("learning_group_features", {})
                .get("display_order", 999),
            }
        )
    group_records.sort(key=lambda group: group["display_order"])

    output_dir = args.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "objects").mkdir(parents=True)

    lookup_meta = write_json(
        output_dir / "lookup.json",
        {"version": 1, "objects": lookup_objects},
    )
    lookup_meta["path"] = "lookup.json"
    shard_metadata = {}
    for shard, objects in sorted(details_by_shard.items()):
        path = output_dir / "objects" / f"{shard}.json"
        meta = write_json(path, {"version": 1, "objects": objects})
        meta["path"] = f"objects/{shard}.json"
        meta["object_count"] = len(objects)
        shard_metadata[shard] = meta

    manifest = {
        "package_version": 1,
        "lookup": lookup_meta,
        "object_shard_algorithm": "sha256(language_object_id) modulo 64",
        "object_shards": shard_metadata,
        "conjugation": {
            "groups": group_records,
            "forms_by_lemma_and_tense": forms_by_lemma_and_tense,
        },
        "counts": {
            "lookup_objects": len(lookup_objects),
            "detail_objects": len(object_rows),
            "detail_shards": len(shard_metadata),
        },
    }
    manifest_meta = write_json(output_dir / "manifest.json", manifest)
    print(
        "Exported "
        f"{len(lookup_objects)} lookup objects and {len(object_rows)} detail objects "
        f"across {len(shard_metadata)} shards to {output_dir} "
        f"({manifest_meta['bytes']} byte manifest)."
    )


if __name__ == "__main__":
    main()

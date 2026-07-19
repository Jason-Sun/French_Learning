#!/usr/bin/env python3
"""Import Kaikki French IPA, variants, and audio metadata into Pronunciation Objects.

Kaikki remains an evidence-backed source.  This importer adds source IPA and
audio metadata to existing canonical words/forms only; it never creates a new
lexical identity or treats browser TTS as pronunciation knowledge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

from canonical_identity import NAMESPACE
from pronunciation_model import ensure_pronunciation_object, ensure_representation_schema, stable_id


KAIKKI_TO_GRAPH_POS = {
    "noun": "NOM", "verb": "VER", "adj": "ADJ", "adv": "ADV", "pron": "PRO",
    "prep": "PRP", "conj": "KON", "intj": "INT", "article": "DET:ART",
}


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_levels(manifest: dict) -> tuple[str, ...]:
    selection = manifest["import"].get("selection", {})
    raw = selection.get("levels") or [selection.get("level", "A1")]
    levels = tuple(sorted({str(level).strip() for level in raw if str(level).strip()}))
    if not levels or any(level not in {"A1", "A2", "B1", "B2", "C1", "C2"} for level in levels):
        raise ValueError(f"Invalid CEFR selection: {levels!r}")
    return levels


def target_pos(entry: dict, words: dict[tuple[str, str], sqlite3.Row], reconciliations: dict[tuple[str, str], str]) -> str | None:
    source_pos = entry.get("pos")
    word = normalize(entry.get("word", ""))
    if source_pos != "det":
        reconciled = reconciliations.get((word, source_pos))
        if reconciled and (word, reconciled) in words:
            return reconciled
        exact = KAIKKI_TO_GRAPH_POS.get(source_pos)
        return exact if exact and (word, exact) in words else None
    candidates = [pos for pos in ("DET:ART", "DET:POS") if (word, pos) in words]
    if len(candidates) == 1:
        return candidates[0]
    reconciled = reconciliations.get((word, source_pos))
    return reconciled if reconciled and (word, reconciled) in words else None


def clean_ipa(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] in "/[" and value[-1] in "/]":
        value = value[1:-1].strip()
    return value or None


def sound_metadata(sound: dict, *, scope: str, form_tags: list[str] | None = None) -> dict:
    metadata = {
        "scope": scope,
        "source_catalog": "kaikki-enwiktionary",
        "tags": [tag for tag in sound.get("tags", []) if isinstance(tag, str)],
    }
    if sound.get("note"):
        metadata["note"] = sound["note"]
    if form_tags:
        metadata["form_tags"] = form_tags
    return metadata


def insert_representation(
    db: sqlite3.Connection,
    *,
    pronunciation_id: str,
    kind: str,
    system: str,
    value_text: str,
    metadata: dict,
    lifecycle: str,
    source_record_id: str,
) -> bool:
    metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    representation_id = stable_id(
        "pronunciation-representation",
        f"{pronunciation_id}|{kind}|{system}|{value_text}|{metadata_json}",
    )
    before = db.execute(
        "SELECT 1 FROM pronunciation_representations WHERE id = ?", (representation_id,)
    ).fetchone() is not None
    db.execute(
        """INSERT INTO pronunciation_representations
           (id, pronunciation_object_id, representation_kind, transcription_system,
            value_text, value_json, lifecycle, confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)
           ON CONFLICT(id) DO UPDATE SET lifecycle = excluded.lifecycle, confidence = excluded.confidence""",
        (representation_id, pronunciation_id, kind, system, value_text, metadata_json, lifecycle),
    )
    db.execute(
        """INSERT OR IGNORE INTO pronunciation_representation_evidence
           (representation_id, source_record_id, confidence) VALUES (?, ?, 1)""",
        (representation_id, source_record_id),
    )
    return not before


def add_sounds(
    db: sqlite3.Connection,
    sounds: list[dict],
    *,
    pronunciation_id: str,
    source_record_id: str,
    scope: str,
    form_tags: list[str] | None,
    counters: Counter,
) -> None:
    for sound in sounds:
        if not isinstance(sound, dict):
            continue
        metadata = sound_metadata(sound, scope=scope, form_tags=form_tags)
        ipa = clean_ipa(sound.get("ipa"))
        if ipa:
            if insert_representation(
                db,
                pronunciation_id=pronunciation_id,
                kind="ipa",
                system="ipa",
                value_text=ipa,
                metadata={**metadata, "raw_ipa": sound["ipa"]},
                lifecycle="canonical",
                source_record_id=source_record_id,
            ):
                counters["ipa_representations_imported"] += 1
        elif sound.get("ipa") is not None:
            counters["invalid_ipa_values"] += 1

        audio_url = sound.get("ogg_url") or sound.get("mp3_url")
        if audio_url:
            audio_metadata = {
                **metadata,
                "audio": sound.get("audio"),
                "ogg_url": sound.get("ogg_url"),
                "mp3_url": sound.get("mp3_url"),
            }
            if insert_representation(
                db,
                pronunciation_id=pronunciation_id,
                kind="audio_url",
                system="wikimedia_commons",
                value_text=audio_url,
                metadata=audio_metadata,
                lifecycle="canonical",
                source_record_id=source_record_id,
            ):
                counters["audio_url_representations_imported"] += 1
        elif sound.get("audio"):
            counters["audio_without_url"] += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if sha256(args.source) != manifest["release"]["sha256"]:
        raise ValueError("Kaikki source SHA-256 mismatch")

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    ensure_representation_schema(db)
    catalog, release = manifest["catalog"], manifest["release"]
    levels = selected_levels(manifest)
    level_key = "-".join(level.casefold() for level in levels)
    run_id = f"import:{release['id']}:{level_key}-pronunciation"
    db.execute(
        "INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES ('kaikki-enwiktionary',?,?,?,?)",
        (catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
    )
    db.execute(
        """INSERT OR IGNORE INTO source_catalogs
           (id,name,homepage_url,license,attribution_text) VALUES (?,?,?,?,?)""",
        (catalog["id"], catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]),
    )
    db.execute(
        """INSERT OR IGNORE INTO source_releases
           (id,catalog_id,release_label,artifact_uri,sha256,scope_description)
           VALUES (?,?,?,?,?,?)""",
        (release["id"], catalog["id"], release["label"], release["artifact_uri"], release["sha256"], release["scope"]),
    )
    db.execute(
        """INSERT OR IGNORE INTO import_runs
           (id,release_id,importer_name,importer_version,status,completed_at)
           VALUES (?,?,?,?, 'completed', CURRENT_TIMESTAMP)""",
        (run_id, release["id"], manifest["import"]["adapter"], manifest["import"]["adapter_version"]),
    )
    placeholders = ",".join("?" for _ in levels)
    words = {
        (normalize(row["canonical_form"]), row["part_of_speech"]): row
        for row in db.execute(
            f"""SELECT object.id, object.canonical_form, object.display_form,
                       object.part_of_speech, canonical.canonical_id
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
    counters: Counter = Counter()
    matched_owners: set[str] = set()
    matched_forms: set[str] = set()
    db.commit()
    db.execute("DELETE FROM import_exclusions WHERE import_run_id = ?", (run_id,))
    db.commit()
    db.execute("BEGIN")
    try:
        with args.source.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                entry = json.loads(line)
                if entry.get("lang_code") != "fr" or not entry.get("word"):
                    continue
                part_of_speech = target_pos(entry, words, reconciliations)
                if not part_of_speech:
                    continue
                owner = words[(normalize(entry["word"]), part_of_speech)]
                sounds = entry.get("sounds") or []
                forms = entry.get("forms") or []
                if not sounds and not any(isinstance(form, dict) and form.get("ipa") for form in forms):
                    continue
                counters["matched_source_entries"] += 1
                record_payload = {"word": entry["word"], "pos": entry.get("pos"), "sounds": sounds, "forms": forms}
                record_id = stable_id("source-record", f"{release['id']}|pronunciation:line:{line_number}")
                db.execute(
                    """INSERT OR IGNORE INTO source_records
                       (id,release_id,external_key,record_kind,content_hash)
                       VALUES (?, ?, ?, 'pronunciation_entry', ?)""",
                    (record_id, release["id"], f"line:{line_number}", hashlib.sha256(json.dumps(record_payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()),
                )
                pronunciation_id, relationship_id = ensure_pronunciation_object(
                    db, owner["id"], display_form=owner["display_form"]
                )
                db.execute(
                    "INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,confidence) VALUES (?, ?, 1)",
                    (relationship_id, record_id),
                )
                db.execute(
                    """INSERT OR IGNORE INTO import_record_mappings
                       (import_run_id,source_record_id,canonical_id,mapping_kind,confidence)
                       VALUES (?, ?, ?, 'kaikki_pronunciation_owner', 1)""",
                    (run_id, record_id, owner["canonical_id"]),
                )
                add_sounds(db, sounds, pronunciation_id=pronunciation_id, source_record_id=record_id, scope="lemma", form_tags=None, counters=counters)
                matched_owners.add(owner["id"])

                for form in forms:
                    if not isinstance(form, dict) or not form.get("form"):
                        continue
                    form_sounds = ([{"ipa": form["ipa"], "tags": form.get("tags", [])}] if form.get("ipa") else [])
                    if not form_sounds:
                        continue
                    targets = list(
                        db.execute(
                            """SELECT form.id, form.display_form, canonical.canonical_id
                               FROM language_objects form
                               JOIN relationships link ON link.source_object_id = form.id
                               JOIN canonical_objects canonical ON canonical.language_object_id = form.id
                               WHERE form.type_code = 'inflected_form'
                                 AND link.relationship_type_code = 'inflected_form_of'
                                 AND link.target_object_id = ?
                                 AND form.normalized_form = ?""",
                            (owner["id"], normalize(form["form"])),
                        )
                    )
                    for target in targets:
                        form_pronunciation_id, form_relationship_id = ensure_pronunciation_object(
                            db, target["id"], display_form=target["display_form"]
                        )
                        db.execute(
                            "INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,confidence) VALUES (?, ?, 1)",
                            (form_relationship_id, record_id),
                        )
                        db.execute(
                            """INSERT OR IGNORE INTO import_record_mappings
                               (import_run_id,source_record_id,canonical_id,mapping_kind,confidence)
                               VALUES (?, ?, ?, 'kaikki_pronunciation_form_surface', 1)""",
                            (run_id, record_id, target["canonical_id"]),
                        )
                        add_sounds(db, form_sounds, pronunciation_id=form_pronunciation_id, source_record_id=record_id, scope="inflected_form", form_tags=form.get("tags") or [], counters=counters)
                        matched_forms.add(target["id"])

        db.execute(
            """UPDATE pronunciation_representations AS derived
               SET lifecycle = 'superseded'
               WHERE derived.representation_kind = 'ipa'
                 AND derived.transcription_system = 'lexique383_derived_ipa_v1'
                 AND EXISTS (
                   SELECT 1 FROM pronunciation_representations AS verified
                   WHERE verified.pronunciation_object_id = derived.pronunciation_object_id
                     AND verified.representation_kind = 'ipa'
                     AND verified.transcription_system = 'ipa'
                     AND verified.lifecycle = 'canonical'
                 )"""
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {
        "release_id": release["id"],
        "selection": {"levels": list(levels)},
        "matched_source_entries": counters["matched_source_entries"],
        "owner_objects_with_kaikki_pronunciation": len(matched_owners),
        "inflected_form_objects_with_kaikki_pronunciation": len(matched_forms),
        "ipa_representations_imported": counters["ipa_representations_imported"],
        "audio_url_representations_imported": counters["audio_url_representations_imported"],
        "invalid_ipa_values": counters["invalid_ipa_values"],
        "audio_without_url": counters["audio_without_url"],
        "audio_playback_implemented": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

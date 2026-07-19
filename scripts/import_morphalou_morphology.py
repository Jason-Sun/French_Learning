#!/usr/bin/env python3
"""Import Morphalou 3.1 morphology for existing, CEFR-scoped verb objects.

FLELex remains Liens' CEFR and lexical-identity authority.  Morphalou never
creates a fallback word: it contributes complete, source-backed inflected-form
analyses only when its normalized verb lemma exactly resolves to an existing
FLELex verb identity in the selected level scope.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import unicodedata
import uuid
import zipfile
from io import TextIOWrapper
from pathlib import Path

from canonical_identity import NAMESPACE, canonical_uuid


MOODS = {
    "indicative": "indicative",
    "subjunctive": "subjunctive",
    "conditional": "conditional",
    "imperative": "imperative",
    "infinitive": "infinitive",
    "participle": "participle",
}
TENSES = {
    "present": "present",
    "imperfect": "imperfect",
    "future": "future",
    "simplePast": "past",
    "past": "past",
}
NUMBERS = {"singular": "singular", "plural": "plural"}
PERSONS = {"firstPerson": "1", "secondPerson": "2", "thirdPerson": "3"}
GENDERS = {"masculine": "masculine", "feminine": "feminine", "invariable": "invariable"}
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def stable(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_levels(manifest: dict) -> tuple[str, ...]:
    levels = tuple(manifest["import"]["selection"].get("levels", ()))
    if not levels or any(level not in VALID_LEVELS for level in levels):
        raise ValueError(f"Invalid CEFR selection: {levels!r}")
    return levels


def rows(source: Path):
    """Yield expanded Morphalou CSV records after its 16-line preamble."""
    if source.suffix.casefold() == ".zip":
        archive = zipfile.ZipFile(source)
        member = next((name for name in archive.namelist() if name.endswith("/Morphalou3.1_CSV.csv")), None)
        if member is None:
            raise ValueError("Morphalou archive does not contain Morphalou3.1_CSV.csv")
        stream = TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="")
    else:
        archive = None
        stream = source.open(encoding="utf-8-sig", newline="")
    try:
        reader = csv.reader(stream, delimiter=";")
        for _ in range(16):
            next(reader)
        lemma: dict[str, str] | None = None
        for line_number, fields in enumerate(reader, start=17):
            if len(fields) != 18:
                raise ValueError(f"Unexpected Morphalou CSV structure at line {line_number}")
            if fields[0]:
                lemma = {
                    "surface": fields[0],
                    "id": fields[1],
                    "category": fields[2],
                    "subcategory": fields[3],
                    "gender": fields[5],
                    "pronunciation": fields[7],
                    "origins": fields[8],
                }
            if lemma is None:
                raise ValueError(f"Inflection before lemma at line {line_number}")
            yield line_number, lemma, {
                "surface": fields[9],
                "id": fields[10],
                "number": fields[11],
                "mood": fields[12],
                "gender": fields[13],
                "tense": fields[14],
                "person": fields[15],
                "pronunciation": fields[16],
                "origins": fields[17],
            }
    finally:
        stream.close()
        if archive is not None:
            archive.close()


def form_features(form: dict[str, str]) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    mood = MOODS.get(form["mood"])
    tense = TENSES.get(form["tense"])
    person = PERSONS.get(form["person"])
    number = NUMBERS.get(form["number"])
    gender = GENDERS.get(form["gender"])
    return mood, tense, person, number, gender


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True, help="Pinned Morphalou3.1 CSV ZIP archive (or extracted CSV for diagnostic use)")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    release = manifest["release"]
    catalog = manifest["catalog"]
    levels = selected_levels(manifest)
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    source_hash = sha256(args.source)
    if source_hash != release["sha256"]:
        raise ValueError("Morphalou source SHA-256 mismatch")
    run_id = f"import:{release['id']}:{'-'.join(level.casefold() for level in levels)}-morphology"

    db.execute("INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES ('morphalou31',?,?,?,?)", (catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]))
    db.execute("INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text) VALUES (?,?,?,?,?)", (catalog["id"], catalog["name"], catalog["homepage_url"], catalog["license"], catalog["attribution_text"]))
    db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,sha256,scope_description) VALUES (?,?,?,?,?,?)", (release["id"], catalog["id"], release["label"], release["artifact_uri"], release["sha256"], release["scope_description"]))
    db.execute("INSERT OR REPLACE INTO import_runs(id,release_id,importer_name,importer_version,configuration_hash,status,completed_at) VALUES (?,?,?,?,?,'completed',CURRENT_TIMESTAMP)", (run_id, release["id"], manifest["import"]["adapter"], manifest["import"]["adapter_version"], source_hash))
    for code, kind, label in [
        ("inflected_form_of", "object", "Inflected form of"),
        ("mood", "code", "Mood"),
        ("tense", "code", "Tense"),
        ("grammatical_person", "code", "Grammatical person"),
        ("grammatical_number", "code", "Grammatical number"),
        ("grammatical_gender", "code", "Grammatical gender"),
    ]:
        db.execute("INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)", (code, kind, label, "Imported Morphalou morphology fact."))

    placeholders = ",".join("?" for _ in levels)
    lemma_rows = db.execute(
        f"""SELECT object.id, object.canonical_form, canonical.canonical_id
            FROM language_objects object
            JOIN canonical_objects canonical ON canonical.language_object_id=object.id
            WHERE object.type_code='word' AND object.part_of_speech='VER'
              AND object.cefr_level IN ({placeholders})""",
        levels,
    )
    lemmas = {norm(row["canonical_form"]): (row["id"], row["canonical_id"]) for row in lemma_rows}
    db.commit()

    matched_lemmas: set[str] = set()
    analyses = new_forms = reused_forms = relation_evidence = fact_evidence = skipped_non_finite = skipped_unsupported = 0
    db.execute("BEGIN")
    try:
        for line_number, lemma, form in rows(args.source):
            if lemma["category"] != "Verbe" or norm(lemma["surface"]) not in lemmas:
                continue
            lemma_key = norm(lemma["surface"])
            matched_lemmas.add(lemma_key)
            mood, tense, person, number, gender = form_features(form)
            if not mood:
                skipped_unsupported += 1
                continue
            if mood == "infinitive" and norm(form["surface"]) == lemma_key:
                skipped_non_finite += 1
                continue
            lemma_id, lemma_canonical_id = lemmas[lemma_key]
            record_id = stable("source-record", f"{release['id']}|lemma:{lemma['id']}|form:{form['id']}")
            content = {"lemma": lemma, "form": form, "line": line_number}
            db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)", (record_id, release["id"], f"lemma:{lemma['id']}|form:{form['id']}", "morphology_row", hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()))
            feature_key = "|".join((mood or "", tense or "", person or "", number or "", gender or ""))
            identity_key = f"fr|inflected_form||{norm(form['surface'])}|owner={lemma_canonical_id}|features={feature_key}"
            existing = db.execute("SELECT canonical_id,language_object_id FROM canonical_objects WHERE identity_key=?", (identity_key,)).fetchone()
            if existing:
                form_canonical_id, form_id = existing["canonical_id"], existing["language_object_id"]
                reused_forms += 1
            else:
                form_id = f"fr:form:{lemma_id}:{norm(form['surface']).replace(' ', '_')}:{feature_key.replace('|', ':') or '-'}"
                db.execute("INSERT INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) VALUES (?,?,?,?,?,'morphalou31','metadata_ready','curated')", (form_id, "inflected_form", form["surface"], form["surface"], norm(form["surface"])))
                db.execute("INSERT INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)", (canonical_uuid(identity_key), form_id, "inflected_form", identity_key))
                db.execute("INSERT INTO form_features(object_id,mood,tense,person,number,gender) VALUES (?,?,?,?,?,?)", (form_id, mood, tense, person, number, gender))
                db.execute("INSERT INTO learning_metadata(object_id) VALUES (?)", (form_id,))
                form_canonical_id = canonical_uuid(identity_key)
                new_forms += 1
            db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'morphalou_morphology_match',1.0)", (run_id, record_id, form_canonical_id))
            relation_id = stable("relationship", f"{form_id}|inflected_form_of|{lemma_id}")
            db.execute("INSERT OR IGNORE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1.0)", (relation_id, form_id, lemma_id, "inflected_form_of"))
            relation_id = db.execute(
                "SELECT id FROM relationships WHERE source_object_id=? AND target_object_id=? AND relationship_type_code='inflected_form_of'",
                (form_id, lemma_id),
            ).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1.0)", (relation_id, record_id))
            relation_evidence += db.execute("SELECT changes()").fetchone()[0]
            facts = [("inflected_form_of", "object", lemma_canonical_id)]
            for predicate, value in (("mood", mood), ("tense", tense), ("grammatical_person", person), ("grammatical_number", number), ("grammatical_gender", gender)):
                if value:
                    facts.append((predicate, "code", value))
            for predicate, kind, value in facts:
                fact_id = stable("fact", f"{form_canonical_id}|{predicate}|{value}")
                db.execute("INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)", (fact_id, form_canonical_id, predicate))
                if kind == "object":
                    db.execute("INSERT OR IGNORE INTO fact_object_values(fact_id,value_canonical_id) VALUES (?,?)", (fact_id, value))
                else:
                    db.execute("INSERT OR IGNORE INTO fact_code_values(fact_id,value_code) VALUES (?,?)", (fact_id, value))
                db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1.0)", (fact_id, record_id))
                fact_evidence += db.execute("SELECT changes()").fetchone()[0]
            analyses += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    unmatched = sorted(set(lemmas) - matched_lemmas)
    report = {
        "release_id": release["id"],
        "source_sha256": source_hash,
        "selection": {"levels": list(levels)},
        "selected_verb_lemmas": len(lemmas),
        "matched_verb_lemmas": len(matched_lemmas),
        "unmatched_verb_lemmas": unmatched,
        "form_analyses_imported": analyses,
        "new_canonical_form_objects": new_forms,
        "reused_canonical_form_objects": reused_forms,
        "inflected_form_relationship_evidence_added": relation_evidence,
        "fact_evidence_added": fact_evidence,
        "skipped_lemma_infinitives": skipped_non_finite,
        "skipped_unsupported_morphology_rows": skipped_unsupported,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

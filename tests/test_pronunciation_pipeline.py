#!/usr/bin/env python3
"""Focused regression tests for canonical Kaikki/Lexique pronunciation flow."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_identity import canonical_uuid  # noqa: E402
from derive_lexique_ipa import main as derive_main  # noqa: E402
from import_kaikki_pronunciations import main as kaikki_main  # noqa: E402
from migrate_pronunciation_objects import main as migrate_main  # noqa: E402
from pronunciation_model import ensure_pronunciation_object, ensure_representation_schema, stable_id  # noqa: E402
from project_pronunciation_browser_details import main as project_main  # noqa: E402


class PronunciationPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "graph.sqlite"
        self.source = self.root / "kaikki.jsonl"
        self.manifest = self.root / "manifest.json"
        self.report = self.root / "report.json"
        self._build_database()
        entry = {
            "lang_code": "fr",
            "word": "tuer",
            "pos": "verb",
            "sounds": [
                {"tags": ["France"], "ipa": "/tɥe/"},
                {"tags": ["Quebec"], "ipa": "/t͡sɥe/"},
                {"audio": "Fr-tuer.ogg", "tags": ["France"], "ogg_url": "https://example.test/tuer.ogg", "mp3_url": "https://example.test/tuer.mp3"},
            ],
            "forms": [{"form": "tué", "tags": ["participle", "past"], "ipa": "/tɥe/"}],
        }
        self.source.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")
        self.manifest.write_text(
            json.dumps(
                {
                    "catalog": {"id": "kaikki-enwiktionary", "name": "Kaikki", "homepage_url": "https://kaikki.example", "license": "CC", "attribution_text": "Kaikki test"},
                    "release": {"id": "kaikki-test", "label": "test", "artifact_uri": "https://kaikki.example/test", "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(), "scope": "test"},
                    "import": {"adapter": "kaikki_enwiktionary_pronunciations", "adapter_version": "1", "selection": {"levels": ["A1"]}},
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _build_database(self) -> None:
        db = sqlite3.connect(self.database)
        db.executescript(
            """
            CREATE TABLE language_objects (id TEXT PRIMARY KEY, type_code TEXT NOT NULL, canonical_form TEXT, display_form TEXT, normalized_form TEXT, cefr_level TEXT, part_of_speech TEXT, source_id TEXT, content_status TEXT, provenance TEXT);
            CREATE TABLE canonical_objects (canonical_id TEXT PRIMARY KEY, language_object_id TEXT NOT NULL UNIQUE, object_type_code TEXT, identity_key TEXT UNIQUE);
            CREATE TABLE relationships (id TEXT PRIMARY KEY, source_object_id TEXT NOT NULL, target_object_id TEXT NOT NULL, relationship_type_code TEXT NOT NULL, position INTEGER, source_kind TEXT DEFAULT 'curated', confidence REAL DEFAULT 1, UNIQUE(source_object_id,target_object_id,relationship_type_code));
            CREATE TABLE relationship_evidence (relationship_id TEXT, source_record_id TEXT, confidence REAL, PRIMARY KEY(relationship_id,source_record_id));
            CREATE TABLE sources (id TEXT PRIMARY KEY, name TEXT, url TEXT, license TEXT, citation TEXT);
            CREATE TABLE source_catalogs (id TEXT PRIMARY KEY, name TEXT, homepage_url TEXT, license TEXT, attribution_text TEXT);
            CREATE TABLE source_releases (id TEXT PRIMARY KEY, catalog_id TEXT, release_label TEXT, artifact_uri TEXT, sha256 TEXT, scope_description TEXT);
            CREATE TABLE source_records (id TEXT PRIMARY KEY, release_id TEXT, external_key TEXT, record_kind TEXT, content_hash TEXT, UNIQUE(release_id,external_key,record_kind));
            CREATE TABLE import_runs (id TEXT PRIMARY KEY, release_id TEXT, importer_name TEXT, importer_version TEXT, configuration_hash TEXT, started_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT, status TEXT);
            CREATE TABLE import_exclusions (import_run_id TEXT, source_record_id TEXT, reason_code TEXT, explanation TEXT, UNIQUE(import_run_id,source_record_id,reason_code));
            CREATE TABLE import_record_mappings (import_run_id TEXT, source_record_id TEXT, canonical_id TEXT, mapping_kind TEXT, confidence REAL, UNIQUE(import_run_id,source_record_id,canonical_id,mapping_kind));
            CREATE TABLE pronunciations (id TEXT PRIMARY KEY, object_id TEXT, ipa TEXT, syllables_json TEXT DEFAULT '[]', stress_json TEXT DEFAULT '[]', variant_code TEXT, audio_source_uri TEXT, local_audio_path TEXT, source_id TEXT, provenance TEXT DEFAULT 'curated', confidence REAL, status TEXT DEFAULT 'metadata_ready');
            """
        )
        db.execute("INSERT INTO language_objects VALUES ('fr:word:tuer:ver','word','tuer','tuer','tuer','A1','VER',NULL,'curated','curated')")
        db.execute("INSERT INTO language_objects VALUES ('fr:form:tué:ver','inflected_form','tué','tué','tué','A1','VER',NULL,'curated','curated')")
        for object_id, kind, key in (("fr:word:tuer:ver", "word", "fr|word|tuer|VER"), ("fr:form:tué:ver", "inflected_form", "fr|form|tué|VER")):
            db.execute("INSERT INTO canonical_objects VALUES (?,?,?,?)", (canonical_uuid(key), object_id, kind, key))
        db.execute("INSERT INTO relationships VALUES ('form-link','fr:form:tué:ver','fr:word:tuer:ver','inflected_form_of',NULL,'curated',1)")
        db.execute("INSERT INTO source_catalogs VALUES ('lexique383','Lexique',NULL,NULL,NULL)")
        db.execute("INSERT INTO source_releases VALUES ('lexique-test','lexique383','test',NULL,NULL,NULL)")
        db.execute("INSERT INTO source_records VALUES ('lexique-row','lexique-test','line:1','lexique_row','hash')")
        ensure_representation_schema(db)
        legacy_pron = "fr:pronunciation:lexique383:word:tuer:ver"
        db.execute("INSERT INTO language_objects VALUES (?,?,?,?,?,?,?,?,?,?)", (legacy_pron, "pronunciation", "tuer pronunciation", "tuer pronunciation", "tuer pronunciation", None, None, "lexique383", "metadata_ready", "curated"))
        db.execute("INSERT INTO canonical_objects VALUES (?,?,?,?)", (canonical_uuid("old-lexique-tuer"), legacy_pron, "pronunciation", "old-lexique-tuer"))
        db.execute("INSERT INTO relationships VALUES ('old-pron-link','fr:word:tuer:ver',?,'has_pronunciation',NULL,'curated',1)", (legacy_pron,))
        db.execute("INSERT INTO relationship_evidence VALUES ('old-pron-link','lexique-row',1)")
        rep = stable_id("pronunciation-representation", "old|phon")
        db.execute("INSERT INTO pronunciation_representations VALUES (?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", (rep, legacy_pron, "phonological_code", "lexique383", "t8e", None, "canonical", 1))
        db.execute("INSERT INTO pronunciation_representation_evidence VALUES (?, 'lexique-row', 1)", (rep,))
        db.commit()
        db.close()

    def run_script(self, function, *arguments: str) -> None:
        old = sys.argv
        try:
            sys.argv = ["script", *arguments]
            function()
        finally:
            sys.argv = old

    def test_kaikki_is_canonical_and_lexique_is_superseded(self) -> None:
        self.run_script(migrate_main, "--database", str(self.database))
        self.run_script(derive_main, "--database", str(self.database))
        self.run_script(kaikki_main, "--database", str(self.database), "--source", str(self.source), "--manifest", str(self.manifest), "--report", str(self.report))
        self.run_script(derive_main, "--database", str(self.database))
        self.run_script(project_main, "--database", str(self.database))
        db = sqlite3.connect(self.database)
        db.row_factory = sqlite3.Row
        pronunciation_id = "fr:pronunciation:word:tuer:ver"
        kinds = {(row["representation_kind"], row["transcription_system"], row["lifecycle"]) for row in db.execute("SELECT representation_kind,transcription_system,lifecycle FROM pronunciation_representations WHERE pronunciation_object_id=?", (pronunciation_id,))}
        self.assertIn(("phonological_code", "lexique383", "canonical"), kinds)
        self.assertIn(("ipa", "ipa", "canonical"), kinds)
        self.assertIn(("audio_url", "wikimedia_commons", "canonical"), kinds)
        self.assertIn(("ipa", "lexique383_derived_ipa_v1", "superseded"), kinds)
        detail = db.execute("SELECT ipa,review_status,transcription_system FROM pronunciation_object_details WHERE object_id=?", (pronunciation_id,)).fetchone()
        self.assertEqual((detail["ipa"], detail["review_status"], detail["transcription_system"]), ("tɥe", "verified", "ipa"))
        form = db.execute("""SELECT detail.ipa FROM pronunciation_object_details detail
                           JOIN relationships edge ON edge.target_object_id=detail.object_id
                           WHERE edge.source_object_id='fr:form:tué:ver'""").fetchone()
        self.assertEqual(form[0], "tɥe")
        legacy = db.execute(
            "SELECT content_status FROM language_objects WHERE id LIKE 'fr:pronunciation:lexique383:%'"
        ).fetchone()
        self.assertEqual(legacy[0], "deprecated")
        self.assertEqual(
            db.execute(
                "SELECT COUNT(*) FROM pronunciation_representations "
                "WHERE pronunciation_object_id LIKE 'fr:pronunciation:lexique383:%'"
            ).fetchone()[0],
            0,
        )
        db.close()


if __name__ == "__main__":
    unittest.main()

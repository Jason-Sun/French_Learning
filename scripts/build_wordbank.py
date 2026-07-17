#!/usr/bin/env python3
"""Build the local Liens A1–B2 French wordbank from FLELex / Beacco.

The resulting SQLite file is deliberately usable without an API or an AI call.
FLELex supplies CEFR level, part of speech, and frequency; authored learning
content lives in the same database and AI additions can be marked separately.
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

LEVELS = {"A1", "A2", "B1", "B2"}


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL,
  license TEXT NOT NULL, citation TEXT NOT NULL
);
CREATE TABLE lexemes (
  id INTEGER PRIMARY KEY,
  lemma TEXT NOT NULL,
  normalized_lemma TEXT NOT NULL,
  part_of_speech TEXT NOT NULL,
  cefr_level TEXT NOT NULL CHECK (cefr_level IN ('A1','A2','B1','B2')),
  frequency_per_million REAL NOT NULL,
  gender TEXT CHECK (gender IN ('m','f','mf')),
  pronunciation_ipa TEXT,
  source_id TEXT NOT NULL REFERENCES sources(id),
  content_status TEXT NOT NULL DEFAULT 'metadata_ready'
    CHECK (content_status IN ('metadata_ready','curated','ai_enriched','reviewed')),
  UNIQUE(normalized_lemma, part_of_speech)
);
CREATE INDEX lexemes_lookup ON lexemes(normalized_lemma);
CREATE TABLE senses (
  id INTEGER PRIMARY KEY,
  lexeme_id INTEGER NOT NULL REFERENCES lexemes(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 1,
  english_gloss TEXT,
  chinese_gloss TEXT,
  learner_note_en TEXT,
  learner_note_zh TEXT,
  source_kind TEXT NOT NULL DEFAULT 'curated'
    CHECK (source_kind IN ('curated','ai_enriched','user_corrected')),
  confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
  UNIQUE(lexeme_id, position)
);
CREATE TABLE forms (
  id INTEGER PRIMARY KEY,
  lexeme_id INTEGER NOT NULL REFERENCES lexemes(id) ON DELETE CASCADE,
  surface TEXT NOT NULL,
  normalized_surface TEXT NOT NULL,
  mood TEXT, tense TEXT, person TEXT, number TEXT, gender TEXT,
  UNIQUE(lexeme_id, normalized_surface, mood, tense, person, number, gender)
);
CREATE INDEX forms_lookup ON forms(normalized_surface);
CREATE TABLE collocations (
  id INTEGER PRIMARY KEY,
  text TEXT NOT NULL, normalized_text TEXT NOT NULL UNIQUE,
  english_gloss TEXT, chinese_gloss TEXT, cefr_level TEXT,
  content_status TEXT NOT NULL DEFAULT 'curated'
);
CREATE TABLE lexeme_collocations (
  lexeme_id INTEGER NOT NULL REFERENCES lexemes(id) ON DELETE CASCADE,
  collocation_id INTEGER NOT NULL REFERENCES collocations(id) ON DELETE CASCADE,
  relation TEXT NOT NULL DEFAULT 'common_with',
  PRIMARY KEY (lexeme_id, collocation_id)
);
CREATE TABLE grammar_patterns (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE, cefr_level TEXT NOT NULL,
  explanation_en TEXT NOT NULL, explanation_zh TEXT
);
CREATE TABLE examples (
  id INTEGER PRIMARY KEY,
  french TEXT NOT NULL UNIQUE, english TEXT NOT NULL, chinese TEXT,
  cefr_level TEXT NOT NULL, source_kind TEXT NOT NULL DEFAULT 'curated'
);
CREATE TABLE example_lexemes (
  example_id INTEGER NOT NULL REFERENCES examples(id) ON DELETE CASCADE,
  lexeme_id INTEGER NOT NULL REFERENCES lexemes(id) ON DELETE CASCADE,
  PRIMARY KEY (example_id, lexeme_id)
);
CREATE VIRTUAL TABLE lexeme_search USING fts5(lemma, normalized_lemma, content='lexemes', content_rowid='id');
CREATE TRIGGER lexemes_ai AFTER INSERT ON lexemes BEGIN
  INSERT INTO lexeme_search(rowid, lemma, normalized_lemma) VALUES (new.id, new.lemma, new.normalized_lemma);
END;
"""

CURATED = {
    "être": ("to be", "是；处于", "Names identity, state, location, and serves as an auxiliary for several movement verbs."),
    "avoir": ("to have", "有；拥有", "Also builds many compound tenses as an auxiliary."),
    "aller": ("to go", "去；将要", "With an infinitive, it forms the near future: aller + infinitive."),
    "faire": ("to do; to make", "做；制作", "A high-frequency irregular verb used in many fixed expressions."),
    "pouvoir": ("can; to be able to", "能够；可以", "Usually followed by an infinitive to express ability or permission."),
    "vouloir": ("to want", "想要", "Use the conditional je voudrais to make requests more polite."),
    "devoir": ("must; to have to", "必须；应该", "Expresses obligation or strong likelihood depending on context."),
    "venir": ("to come", "来", "Venir de + infinitive expresses the recent past."),
    "prendre": ("to take", "拿；乘坐；花费", "Its meaning changes naturally in common expressions and collocations."),
    "mettre": ("to put; to place", "放；穿；花费", "A common irregular verb with many everyday uses."),
    "savoir": ("to know; to know how", "知道；会", "Savoir concerns facts or learned ability; connaître concerns familiarity."),
    "connaître": ("to know; to be familiar with", "认识；了解", "Use for people, places, and things you are familiar with."),
    "parler": ("to speak", "说；交谈", "Parler de means to talk about; parler à means to speak to someone."),
    "apprendre": ("to learn; to teach", "学习；教", "Apprendre quelque chose means learn something; apprendre à quelqu'un means teach someone."),
    "comprendre": ("to understand", "理解", "Comprendre que introduces a complete idea or clause."),
    "temps": ("time; weather", "时间；天气", "The intended meaning is determined by context: le temps passes; quel temps fait-il? asks about weather."),
    "personne": ("person; nobody", "人；没有人", "With ne, personne means nobody; without it, it means a person."),
    "chose": ("thing", "事情；东西", "Often appears in quelque chose, meaning something."),
    "raison": ("reason", "原因；理由", "Avoir raison means to be right."),
    "travail": ("work; job", "工作", "Travail is usually masculine and commonly used without an article in expressions."),
}

CURATED_POS = {
    "être": {"VER"}, "avoir": {"VER"}, "aller": {"VER"}, "faire": {"VER"},
    "pouvoir": {"VER"}, "vouloir": {"VER"}, "devoir": {"VER"}, "venir": {"VER"},
    "prendre": {"VER"}, "mettre": {"VER"}, "savoir": {"VER"}, "connaître": {"VER"},
    "parler": {"VER"}, "apprendre": {"VER"}, "comprendre": {"VER"},
    "temps": {"NOM"}, "personne": {"NOM"}, "chose": {"NOM"}, "raison": {"NOM"},
    "travail": {"NOM"},
}

IRREGULAR_FORMS = {
    "être": [("suis", "indicative", "present", "1", "singular"), ("es", "indicative", "present", "2", "singular"), ("est", "indicative", "present", "3", "singular"), ("sommes", "indicative", "present", "1", "plural"), ("êtes", "indicative", "present", "2", "plural"), ("sont", "indicative", "present", "3", "plural")],
    "aller": [("vais", "indicative", "present", "1", "singular"), ("vas", "indicative", "present", "2", "singular"), ("va", "indicative", "present", "3", "singular"), ("allons", "indicative", "present", "1", "plural"), ("allez", "indicative", "present", "2", "plural"), ("vont", "indicative", "present", "3", "plural")],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="FLELex_TreeTagger_Beacco.txt")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    db = sqlite3.connect(args.output)
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO metadata VALUES (?, ?)", [
        ("schema_version", "1"), ("selection_rule", "FLELex / Beacco CEFR classification A1 through B2 inclusive"),
        ("explanation_policy", "English is always stored; Chinese is optional at display time."),
    ])
    db.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?)", (
        "flelex-beacco-2025", "FLELex / Beacco", "https://cental.uclouvain.be/cefrlex/flelex/download/",
        "CC BY-NC-SA 4.0", "Pintard, A. and François, T. (2020). Combining expert knowledge with frequency information to infer CEFR levels for words."
    ))
    with args.source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            level = row["level"].strip()
            lemma = row["word"].strip()
            if level not in LEVELS or not lemma or re.fullmatch(r"[\W_]+", lemma):
                continue
            pos = row["tag"].strip()
            curated = CURATED.get(normalise(lemma))
            if curated and pos not in CURATED_POS[normalise(lemma)]:
                curated = None
            status = "curated" if curated else "metadata_ready"
            cursor = db.execute(
                "INSERT OR IGNORE INTO lexemes (lemma, normalized_lemma, part_of_speech, cefr_level, frequency_per_million, source_id, content_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (lemma, normalise(lemma), pos, level, float(row["freq_total"] or 0), "flelex-beacco-2025", status),
            )
            if curated and cursor.rowcount:
                db.execute("INSERT INTO senses (lexeme_id, english_gloss, chinese_gloss, learner_note_en) VALUES (?, ?, ?, ?)", (cursor.lastrowid, *curated))
    for lemma, forms in IRREGULAR_FORMS.items():
        row = db.execute("SELECT id FROM lexemes WHERE normalized_lemma = ? AND part_of_speech IN ('VER', 'V') LIMIT 1", (lemma,)).fetchone()
        if row:
            db.executemany("INSERT OR IGNORE INTO forms (lexeme_id, surface, normalized_surface, mood, tense, person, number) VALUES (?, ?, ?, ?, ?, ?, ?)", [(row[0], surface, normalise(surface), mood, tense, person, number) for surface, mood, tense, person, number in forms])
    db.execute("INSERT INTO grammar_patterns (name, cefr_level, explanation_en, explanation_zh) VALUES (?, ?, ?, ?)", ("passé composé with être", "A2", "Movement verbs such as aller commonly use être as their auxiliary; the past participle agrees with the subject.", "像 aller 这样的移动动词在复合过去时中常用 être 作助动词；过去分词与主语保持性数一致。"))
    db.commit()
    count = db.execute("SELECT count(*) FROM lexemes").fetchone()[0]
    curated_count = db.execute("SELECT count(*) FROM senses").fetchone()[0]
    print(f"Built {args.output} with {count} A1–B2 lexemes and {curated_count} authored starter senses.")


if __name__ == "__main__":
    main()

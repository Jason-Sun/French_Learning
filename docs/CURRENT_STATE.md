# Liens Current State

**Snapshot date:** 2026-07-17  
**Canonical product branch:** `Liens_dev`
**Current milestone:** A1 Golden Slice — source-backed graph enrichment

## Implemented

- Static browser app with direct local Language Object search and sentence routing.
- SQLite graph with stable IDs and typed relationships; browser index export is generated from it.
- 8,767 A1–B2 word objects, 10,627 source-backed inflected-form objects, 96 graph-native conjugation realizations, learning groups/tenses, 41 example sentence objects, grammar structures, teacher resources, and 11,777 Pronunciation Objects.
- Accent-insensitive lookup that preserves canonical French spelling on pages.
- Deterministic Sentence Intelligence for local token resolution, selected contractions/elisions, expressions, grammar patterns, and review candidates.
- Pedagogical conjugation UI for the eight seeded core verbs; data-first support for unfilled future tenses.
- Graph-native IPA and independent pronunciation for all 56 seeded core forms; local recording → local cached TTS → browser synthesis provider chain.
- Optional Chinese display; English always visible; local saved-object state.
- A durable documentation system with product, architecture, roadmap, decision, contributor, and subsystem contracts.
- Refined visual interaction system: shared focus, active, hover, motion, responsive-spacing, touch-target, empty-state, and reduced-motion behavior while preserving the existing visual identity.
- Canonical UUID registry, predicate-based fact/evidence provenance, immutable Learning Resource revisions, and non-canonical parser-analysis boundaries are established before any A1 source import.
- Kaikki's hash-locked English Wiktionary extraction provides 3,301 first-class lexical-sense objects and 3,383 independently evidenced English-gloss facts for 1,222 of the 1,247 A1 words; the 25 unmatched A1 entries are explicit coverage gaps, not generated content.
- The browser export projects ordered lexical senses and renders them on the existing Word Learning page without changing the core navigation model.
- First-class Grammar Language Object taxonomy, semantic grammar relationships, and generic grammar-object analysis matches are established; no new grammar inventory has been imported.
- The official FLELex / Beacco TreeTagger artifact is hash-locked for the A1 baseline: all 1,247 A1 source rows map to canonical objects and evidence their CEFR, part-of-speech, and frequency facts.
- The hash-locked Lexique 3.83 morphology import adds 9,639 distinct source-backed A1 verb-form objects, each connected to its lemma and conjugation paradigm; four conflicting source rows remain explicit exclusions pending review.
- The same Lexique release adds source-backed gender/number inflection analyses for A1 nouns and adjectives; all imported form objects have canonical IDs and lemma links.
- Lexique now also evidences gender/number facts for 33 existing A1 pronoun, article, and possessive-determiner objects. It does not provide the paradigm links needed to connect variants such as `mon` and `ma`, so no relationship has been invented.
- Lexique pronunciation coverage is imported as 11,680 source-labelled phonological-code and syllabification pairs for linked A1 objects. These representations have row-level evidence, are not IPA, and never appear as IPA in the browser.

## Pending

- Broader curated word/form definitions, examples, collocations, and verified-IPA coverage.
- Additional conjugation data and reviewed tense resources.
- Production review scheduling, collection modes, account persistence, and synchronization.
- Reading, listening, writing, and exercise object types/surfaces.
- Local audio assets or local TTS caching.
- Structured AI draft ingestion and human review workflow.
- Production build, deployment, licensing, observability, and privacy policies.

## Known limitations

- This is a static, dependency-free prototype; browser storage is per-device and not account-backed.
- Sentence Intelligence is intentionally deterministic and covers a limited set of grammar patterns.
- Search relies on the browser JSON projection; it does not yet query SQLite directly in-browser.
- Pronunciation has verified IPA only for the initial curated/core set. Lexique's broader A1 code and syllable coverage remains source-labelled until a separately validated IPA conversion or source is available.
- Some imported learning content is explicitly draft/enriched and should not be represented as fully curated.

## Recommended next milestone

Continue the **A1 Golden Slice** with source-backed grammar-network enrichment: canonical grammar objects, prerequisite/contrast links, triggers, and realization through existing forms. Do not introduce unevidenced grammar claims or new lexical data during that milestone.

## Required maintenance

Update this file only when a completed milestone or verified project state makes it inaccurate. Keep counts and branch only when verified from the database/repository; do not estimate them.

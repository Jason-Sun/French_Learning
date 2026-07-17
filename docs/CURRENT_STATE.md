# Liens Current State

**Snapshot date:** 2026-07-17  
**Canonical product branch:** `Liens_dev`
**Current milestone:** Source-independent production lexical foundation

## Implemented

- Static browser app with direct local Language Object search and sentence routing.
- SQLite graph with stable IDs and typed relationships; browser index export is generated from it.
- 8,767 A1–B2 word objects, 56 core inflected forms, 96 graph-native conjugation realizations, learning groups/tenses, 41 example sentence objects, grammar structures, teacher resources, and 97 Pronunciation Objects.
- Accent-insensitive lookup that preserves canonical French spelling on pages.
- Deterministic Sentence Intelligence for local token resolution, selected contractions/elisions, expressions, grammar patterns, and review candidates.
- Pedagogical conjugation UI for the eight seeded core verbs; data-first support for unfilled future tenses.
- Graph-native IPA and independent pronunciation for all 56 seeded core forms; local recording → local cached TTS → browser synthesis provider chain.
- Optional Chinese display; English always visible; local saved-object state.
- A durable documentation system with product, architecture, roadmap, decision, contributor, and subsystem contracts.
- Refined visual interaction system: shared focus, active, hover, motion, responsive-spacing, touch-target, empty-state, and reduced-motion behavior while preserving the existing visual identity.
- Canonical UUID registry, fact/evidence provenance model, and general Learning Layer infrastructure are being introduced before any A1 source import.

## Pending

- Broader curated word/form definitions, examples, collocations, and pronunciation coverage.
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
- Pronunciation has IPA for the initial curated/core set, not full A1–B2 surface-form coverage.
- Some imported learning content is explicitly draft/enriched and should not be represented as fully curated.

## Recommended next milestone

Define the **review and collections architecture**: stable learner-state model, collection boundaries (Vocabulary, Example Sentences, Collocations), and an offline-first review scheduling contract. Do not implement it before an architecture review and approval.

## Required maintenance

Update this file only when a completed milestone or verified project state makes it inaccurate. Keep counts and branch only when verified from the database/repository; do not estimate them.

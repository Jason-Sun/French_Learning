# Liens Current State

**Snapshot date:** 2026-07-17  
**Canonical product branch:** `Liens_dev`
**Current milestone:** Architecture Freeze v1.0 — completed long-term architecture review

## Architecture Freeze v1.0

- The canonical long-term reference is [ARCHITECTURE_FREEZE_V1.md](ARCHITECTURE_FREEZE_V1.md).
- Canonical UUIDs, Object → Fact → Evidence, typed relationships, source independence, first-class grammar, pronunciation representations, and revisioned Learning Resources remain the durable graph foundation.
- The local SQLite graph remains the authoritative runtime representation, but SQLite and browser indexes are designated generated release artifacts once the deterministic build/release pipeline is complete.
- Collections, review, progress, preferences, and sync are explicitly a future user-state domain, separate from the shared canonical graph.
- AI is frozen as a draft/analysis layer: it may not write canonical data without explicit validation, review, and promotion.

### Current architecture gap

The repository still contains generated SQLite and browser-index artifacts, and rebuilding currently requires manual source preparation. Before material A2 expansion or any history migration, Liens needs one deterministic end-to-end data build, immutable release manifests, and artifact distribution outside ordinary Git history.

### Product constitution

[LIENS_BIBLE.md](LIENS_BIBLE.md) is now the highest-level, long-lived product reference. It separates Liens' enduring identity from the active Product Bible and the technical Architecture Freeze.

## Implemented

- Static browser app with direct local Language Object search and sentence routing.
- SQLite graph with stable IDs and typed relationships; browser index export is generated from it.
- 8,767 A1–B2 word objects, 10,627 source-backed inflected-form objects, 96 graph-native conjugation realizations, learning groups/tenses, 41 example sentence objects, grammar structures, teacher resources, and 11,777 Pronunciation Objects.
- Accent-insensitive lookup that preserves canonical French spelling on pages.
- Deterministic Sentence Intelligence for local token resolution, selected contractions/elisions, expressions, grammar patterns, and review candidates.
- Pedagogical conjugation UI for every locally paradigm-linked verb; data-first support for unfilled future tenses.
- A versioned, evidence-backed French verb-group derivation imports 1,630 canonical `verb_group` facts: 1,440 first-group, 5 second-group, and 185 third-group classifications. The 153 `-ir` verbs without the required present-participle evidence remain explicitly unclassified.
- Graph-native IPA and independent pronunciation for all 56 seeded core forms; local recording → local cached TTS → browser synthesis provider chain.
- Optional Chinese display; English always visible; local saved-object state.
- Contextual AI Learning Assistance foundation: a provider-neutral, opt-in browser adapter can render locally cached, clearly labelled AI learning drafts in existing explanation slots. It has no configured provider, no network call, and no canonical graph write path.
- A durable documentation system with product, architecture, roadmap, decision, contributor, and subsystem contracts.
- Refined visual interaction system: shared focus, active, hover, motion, responsive-spacing, touch-target, empty-state, and reduced-motion behavior while preserving the existing visual identity.
- Canonical UUID registry, predicate-based fact/evidence provenance, immutable Learning Resource revisions, and non-canonical parser-analysis boundaries are established before any A1 source import.
- Kaikki's hash-locked English Wiktionary extraction provides 3,301 first-class lexical-sense objects and 3,383 independently evidenced English-gloss facts for 1,222 of the 1,247 A1 words; the 25 unmatched A1 entries are explicit coverage gaps, not generated content.
- Imported Kaikki `has_sense` links and Lexique `has_pronunciation` links now retain their own source records, alongside the evidence held by their facts or pronunciation representations.
- The browser export projects ordered lexical senses and renders them on the existing Word Learning page without changing the core navigation model.
- Multi-sense words now use a progressive in-place Meaning explorer: the lemma remains the anchor, any source-backed sense can expand in place or all panels can be collapsed, only the first four senses appear initially, and a selected panel renders its source-aligned examples. Direct sense routes preserve canonical identity while opening the owner-word context.
- New canonical graph relationship imports now support independent source evidence; legacy edges are retained as compatibility data and will be audited separately.
- The CC-BY Tex grammar index now supplies an evidenced A1 grammar network of eight topics, twelve constructions/patterns, and 31 typed graph links.
- Kaikki now contributes 1,903 attributable translated example-sentence objects, 1,911 evidenced `illustrates` links, and 205 source-backed synonym/antonym links for the A1 graph.
- Kaikki phrase entries now contribute 159 source-backed, A1-connected `expression` objects, 177 independently evidenced English translations, and 569 ordered component records. The source calls them phrases, so Liens does not mislabel them as collocations or idioms.
- First-class Grammar Language Object taxonomy, semantic grammar relationships, and generic grammar-object analysis matches are established; no new grammar inventory has been imported.
- The official FLELex / Beacco TreeTagger artifact is hash-locked for the A1 baseline: all 1,247 A1 source rows map to canonical objects and evidence their CEFR, part-of-speech, and frequency facts.
- The hash-locked Lexique 3.83 morphology import adds 9,639 distinct source-backed A1 verb-form objects, each connected to its lemma and conjugation paradigm; four conflicting source rows remain explicit exclusions pending review.
- The tense-paradigm projection now connects 8,262 supported Lexique form analyses to 1,984 verb-specific learning paradigms, enabling local conjugation tables such as `manger → Présent → mange / manges / mangeons` without hard-coded forms. Source tenses outside the learning catalog remain explicit exclusions from the selector.
- All Lexique-created A1 inflection links now carry row-level relationship evidence. Paradigm membership is explicitly marked as a transparent derivation from an asserted form link, rather than represented as a direct source claim.
- The same Lexique release adds source-backed gender/number inflection analyses for A1 nouns and adjectives; all imported form objects have canonical IDs and lemma links.
- Lexique now also evidences gender/number facts for 33 existing A1 pronoun, article, and possessive-determiner objects. It does not provide the paradigm links needed to connect variants such as `mon` and `ma`, so no relationship has been invented.
- Lexique pronunciation coverage is imported as 11,680 source-labelled phonological-code and syllabification pairs for linked A1 objects. These representations have row-level evidence, are not IPA, and never appear as IPA in the browser.
- The A1 Golden Slice audit passes with zero foreign-key, orphaned mapping/alignment/component, duplicate-identity, canonical-fact-evidence, or scoped source-edge-evidence failures. It verifies all 1,247 FLELex A1 baseline rows map to canonical objects.

## Pending

- Broader curated word/form definitions, examples, collocations, and verified-IPA coverage.
- Additional conjugation data and reviewed tense resources.
- Production review scheduling, collection modes, account persistence, and synchronization.
- Reading, listening, writing, and exercise object types/surfaces.
- Local audio assets or local TTS caching.
- Structured AI draft ingestion and human review workflow.
- Secure AI-provider transport, generation-run provenance, privacy/consent policy, and review/promotion workflow for live AI assistance.
- Production build, deployment, licensing, observability, and privacy policies.

## Known limitations

- This is a static, dependency-free prototype; browser storage is per-device and not account-backed.
- Sentence Intelligence is intentionally deterministic and covers a limited set of grammar patterns.
- Search relies on the browser JSON projection; it does not yet query SQLite directly in-browser.
- Pronunciation has verified IPA only for the initial curated/core set. Lexique's broader A1 code and syllable coverage remains source-labelled until a separately validated IPA conversion or source is available.
- Some imported learning content is explicitly draft/enriched and should not be represented as fully curated.
- Source coverage gaps remain explicit rather than fabricated: `bienvenir` has no Lexique form coverage; Kaikki has no matched sense entry for 25 FLELex A1 word/POS identities; 434 Kaikki phrase senses have an unresolved local A1 component and are excluded from expression import.

## Recommended next milestone

Build the **Data Build and Release Foundation**: one pinned, deterministic build through validation, export, audit, and immutable release manifest. Do not migrate generated artifacts out of Git or start material A2 expansion until it is proven.

## Required maintenance

Update this file only when a completed milestone or verified project state makes it inaccurate. Keep counts and branch only when verified from the database/repository; do not estimate them.

# Liens Current State

**Snapshot date:** 2026-07-19
**Canonical product branch:** `Liens_dev`
**Current milestone:** A1–C2 lexical and simple-morphology release — completed

## Architecture Freeze v1.0

- The canonical long-term reference is [ARCHITECTURE_FREEZE_V1.md](ARCHITECTURE_FREEZE_V1.md).
- [MANUAL.md](MANUAL.md) is the comprehensive Architecture & Product Manual for long-term handover; it cross-references the constitutional documents and bounded subsystem contracts without replacing their authority.
- Canonical UUIDs, Object → Fact → Evidence, typed relationships, source independence, first-class grammar, pronunciation representations, and revisioned Learning Resources remain the durable graph foundation.
- The local SQLite graph remains the authoritative runtime representation, but SQLite and browser indexes are designated generated release artifacts once the deterministic build/release pipeline is complete.
- Collections, lightweight local review, progress, preferences, and future sync are a user-state domain, separate from the shared canonical graph.
- AI is frozen as a draft/analysis layer: it may not write canonical data without explicit validation, review, and promotion.

### Current architecture gap

The deterministic release pipeline and external-artifact workflow are now proven. Source preparation remains explicit and local (each build receives checksum-verified upstream artifacts), and the next release concern is automated acquisition, attribution checks, and publishing rather than a redesign of the graph.

### Product constitution

[LIENS_BIBLE.md](LIENS_BIBLE.md) is now the highest-level, long-lived product reference. It separates Liens' enduring identity from the active Product Bible and the technical Architecture Freeze.

## Implemented

- Static browser app with direct local Language Object search and sentence routing.
- SQLite graph with stable IDs and typed relationships; a generated browser package projects it through a 9.3 MB lookup bootstrap and 64 integrity-hashed, lazy detail shards.
- The active A1–C2 release contains 138,734 active source-independent Pronunciation Objects. Kaikki contributes 247,285 verified IPA representations and 41,223 audio URLs retained as metadata; 4,387 clearly labelled Lexique-derived IPA fallbacks remain active only where Kaikki IPA is unavailable. Lexique phonological code and syllabification remain parallel source representations.
- Accent-insensitive lookup that preserves canonical French spelling on pages.
- Deterministic Sentence Intelligence for local token resolution, explicit form analyses, selected contractions/elisions, two-to-five-component expressions, grammar patterns, and review candidates. The sentence first screen separates exact local form observations from matched Grammar Objects; AI receives that deterministic result and may not add a named grammar construction.
- Pedagogical conjugation UI for every locally paradigm-linked verb; data-first support for unfilled future tenses.
- A versioned, evidence-backed French verb-group derivation imports 1,630 canonical `verb_group` facts: 1,440 first-group, 5 second-group, and 185 third-group classifications. The 153 `-ir` verbs without the required present-participle evidence remain explicitly unclassified.
- Graph-native IPA and independent pronunciation for all 56 seeded core forms; local recording → local cached TTS → browser synthesis provider chain.
- Optional Chinese display; English always visible; local saved-object state.
- Vocabulary Library and Personal Learning Layer: Home and the persistent Vocabulary control now open a canonical Vocabulary Library, which indexes every local word/POS identity by A1–C2 and displays exactly 20 entries per page. Each CEFR level also exposes graph-backed learner categories—All, Verbs, Nouns, Adjectives, Adverbs, Function words, and Other—without creating duplicate data. The default learner ordering is highest source-backed frequency first (`Most useful`), with an optional A–Z ordering; category, sort, pagination, and return navigation preserve the learner’s browsing context. Each entry routes to its existing Language Object page. Liens maintains a native-app exploration path: Back and Forward restore scroll position and view state (including vocabulary filters, sort, page, selected senses, and expanded sections), are visible only when available, and a new destination clears the Forward branch. The Liens logo and Home control reset both directions and start a fresh exploration session. Learner-owned saved objects, collection memberships, and review events remain in a separate browser IndexedDB database. The Notebook reads only those saved objects in calm List and Card views, with local previous/next, optional shuffle, direct links back to the original object, and removal; it adds no copied card data or scheduling. Today’s Review remains intentionally lightweight: one calm reconnection per saved item per day, with retained review events but no claimed spaced-repetition algorithm.
- Contextual AI Learning Assistance: the provider-neutral Learning Resource Resolver automatically completes visible missing learning slots with clearly labelled AI drafts when online assistance is available. A dedicated browser IndexedDB AI Learning Database persists learner-scoped resources, revisions, provider/model/prompt-version provenance, lifecycle state, and normalized unknown-lookups separately from the canonical graph. Resolution is canonical source-backed resource → active AI resource → online generation, so repeat visits do not spend tokens. Versioned Core A1 packs now preload non-canonical OpenAI Codex drafts for high-frequency verbs, function words, fixed expressions, and everyday time/place/social vocabulary (English and Simplified Chinese) into that same database, avoiding a Gemini call for those slots without overwriting existing learner resources. Canonical coverage takes precedence and supersedes matching AI history without deleting it. Resource identity includes target, kind, context, language, and stricter resource-contract versions when needed; English and enabled reference languages resolve, cache, label, and revise independently. An unknown lookup is deliberately narrower: it creates one bounded English provisional note, records a local recent lookup, and waits for the learner to request each follow-up or reference-language resource. Local graph analysis always renders first; sentence guidance is constrained by deterministic matches; and drafts never have a canonical graph write path. Gemini is the first development adapter, served through a local environment-key server.
- A durable documentation system with product, architecture, roadmap, decision, contributor, and subsystem contracts.
- Refined visual interaction system: shared focus, active, hover, motion, responsive-spacing, touch-target, empty-state, and reduced-motion behavior while preserving the existing visual identity.
- Canonical UUID registry, predicate-based fact/evidence provenance, immutable Learning Resource revisions, and non-canonical parser-analysis boundaries are established before any A1 source import.
- The combined, hash-locked Kaikki English Wiktionary and complementary French Wiktionary-derived releases currently supply source-backed senses for 8,664 of 8,767 A1–B2 word/POS objects (98.83%). This includes 17,755 lexical-sense objects, 17,657 independently evidenced English-gloss facts, and 296 independently evidenced French source-definition facts. All 8,767 lexical identities remain present and locally resolvable; 103 identities have no exact or explicitly reconciled imported source-backed sense and are retained as coverage gaps rather than filled with generated canonical content.
- Importer reports retain the detailed source/POS mismatches (including the 259 reported for the A2–B2 pass), while `a1-b2-production-graph-audit.json` is the authoritative release-level measurement of the graph after all imports and reconciliations.
- Imported Kaikki `has_sense` links and Lexique `has_pronunciation` links now retain their own source records, alongside the evidence held by their facts or pronunciation representations.
- The browser export projects ordered lexical senses and renders them on the existing Word Learning page without changing the core navigation model.
- Multi-sense words now use a progressive in-place Meaning explorer: the lemma remains the anchor, any source-backed sense can expand in place or all panels can be collapsed, only the first four senses appear initially, and a selected panel renders its source-aligned examples. Direct sense routes preserve canonical identity while opening the owner-word context.
- New canonical graph relationship imports now support independent source evidence; legacy edges are retained as compatibility data and will be audited separately.
- The CC-BY Tex grammar index now supplies an evidenced A1 grammar network of eight topics, twelve constructions/patterns, and 31 typed graph links.
- Kaikki now contributes 4,286 attributable translated example-sentence objects, 4,318 evidenced `illustrates` links, and 1,693 source-backed synonym/antonym links for the A1–B2 graph.
- Kaikki phrase entries now contribute 246 source-backed, A1–B2-connected `expression` objects, 275 independently evidenced English translations, and 913 ordered component records. The source calls them phrases, so Liens does not mislabel them as collocations or idioms; 336 phrase senses with unresolved local components remain explicit exclusions.
- First-class Grammar Language Object taxonomy, semantic grammar relationships, and generic grammar-object analysis matches are established; no new grammar inventory has been imported.
- The official FLELex / Beacco TreeTagger artifact is hash-locked for the A1 baseline: all 1,247 A1 source rows map to canonical objects and evidence their CEFR, part-of-speech, and frequency facts.
- The active external release is `liens-a1-c2-complete-v1`: 14,236 A1–C2 FLELex lexical identities, 160,147 browser lookup objects, 247,048 detail objects across 64 integrity-hashed shards, and a checksum manifest. When served locally with `releases/liens-c1-c2` available, the app now selects it by default; `?graphRoot=releases/liens-c1-c2/browser` remains available to pin that package explicitly.
- Morphalou 3.1 now supplies 131,431 directly evidenced verb-form analyses for the existing 2,598 A1–C2 FLELex verb identities. Combined with compatible source analyses already in the graph, 140,698 distinct inflected-form objects resolve through the local graph. The source-backed simple-form projection creates 23,859 verb-specific tense paradigms and 131,392 evidenced form-membership links.
- The all-level release audit passes with zero foreign-key, orphan, or source-evidence failures. It reports 95.60% source-backed lexical-sense coverage (13,610 of 14,236 word/POS objects). Five FLELex `VER` identities have no linked source form—`bienvenir`, `hier`, `accroire`, `assavoir`, and `étranger`—and remain explicit source gaps rather than receiving fabricated conjugations.
- The hash-locked Lexique 3.83 morphology import adds 9,639 distinct source-backed A1 verb-form objects, each connected to its lemma and conjugation paradigm; four conflicting source rows remain explicit exclusions pending review.
- The same hash-locked Lexique release now covers A1–B2 morphology with 42,042 source-backed analyses and 42,745 linked Lexique form objects across the scoped vocabulary. Its four known conflicting source rows remain recorded as explicit exclusions; every imported form-to-lemma edge has relationship evidence.
- The tense-paradigm projection now connects 8,262 supported Lexique form analyses to 1,984 verb-specific learning paradigms, enabling local conjugation tables such as `manger → Présent → mange / manges / mangeons` without hard-coded forms. Source tenses outside the learning catalog remain explicit exclusions from the selector.
- All Lexique-created A1 inflection links now carry row-level relationship evidence. Paradigm membership is explicitly marked as a transparent derivation from an asserted form link, rather than represented as a direct source claim.
- The same Lexique release adds source-backed gender/number inflection analyses for A1 nouns and adjectives; all imported form objects have canonical IDs and lemma links.
- Lexique now also evidences gender/number facts for 33 existing A1 pronoun, article, and possessive-determiner objects. It does not provide the paradigm links needed to connect variants such as `mon` and `ma`, so no relationship has been invented.
- Lexique pronunciation coverage is imported as 38,252 source-labelled phonological-code and syllabification values for 19,126 linked A1–B2 objects, including 479 of 528 in-scope function words. These representations have row-level evidence, are not IPA, and never appear as IPA in the browser.
- The A1 Golden Slice audit passes with zero foreign-key, orphaned mapping/alignment/component, duplicate-identity, canonical-fact-evidence, or scoped source-edge-evidence failures. It verifies all 1,247 FLELex A1 baseline rows map to canonical objects.

## Pending

- Broader curated word/form definitions, examples, and collocations.
- Source-backed compound conjugation realizations and reviewed tense teaching resources. The current complete morphology release covers source-attested simple forms; it does not fabricate multi-word compound forms.
- Production review scheduling, richer collection modes, account persistence, and synchronization.
- Reading, listening, writing, and exercise object types/surfaces.
- Local audio assets or local TTS caching.
- Structured AI draft ingestion and human review workflow.
- Production AI-provider transport, generation-run provenance, privacy/consent policy, and review/promotion workflow for live AI assistance.
- Production build, deployment, licensing, observability, and privacy policies.

## Known limitations

- This is a static, dependency-free prototype; browser storage is per-device and not account-backed.
- Sentence Intelligence is intentionally deterministic and covers a limited set of grammar patterns.
- Search relies on the browser data-package projection; it does not yet query SQLite directly in-browser.
- Kaikki does not cover every local object with IPA. When a deterministic Lexique conversion is available, the UI labels it **Derived from Lexique** rather than verified; browser TTS remains playback-only. Kaikki audio URLs are stored as metadata and no remote audio playback is enabled.
- Some imported learning content is explicitly draft/enriched and should not be represented as fully curated.
- Canonical grammar coverage remains limited to the attributed Tex A1 index (38 current grammar-related objects). No A2–B2 grammar content has been invented in the absence of an appropriate attributable source.
- Source coverage gaps remain explicit rather than fabricated: five A1–C2 FLELex `VER` identities have no linked source-backed form; 626 A1–C2 word/POS identities currently lack an exact or explicitly reconciled source-backed lexical sense; and phrase-component exclusions remain recorded by their source-scope reports.

## Recommended next milestone

Use the validated A1–C2 release as the baseline for learner-facing quality work: compound-form sourcing, curated teaching resources, sentence coverage, and review-loop evaluation. Keep generated artifacts outside ordinary Git history.

## Required maintenance

Update this file only when a completed milestone or verified project state makes it inaccurate. Keep counts and branch only when verified from the database/repository; do not estimate them.

# Liens Decision Log

This is an append-only record. Amend historical entries only to correct factual errors; record a new decision when direction changes.

## ADR-001 — Language Object Graph as the knowledge source of truth

**Date:** 2026-07 (initial project architecture)  
**Decision:** Model meaningful language elements as stable Language Objects connected through typed relationships in SQLite.  
**Reason:** Words alone cannot represent forms, constructions, sentences, pronunciation, and reusable learning links consistently.  
**Alternatives:** Flat dictionary tables; page-specific JSON; separate isolated vocab/grammar systems.  
**Long-term impact:** New learning content can be added as data and relationships rather than product-specific silos.

## ADR-002 — Local structured resolution before AI

**Date:** 2026-07  
**Decision:** Resolve known language material locally; reserve AI for explicit, structured draft enrichment.  
**Reason:** Core learning knowledge must be reliable, fast, explainable, and usable without an AI call.  
**Alternatives:** Chatbot-first analysis; AI as dictionary source.  
**Long-term impact:** AI cannot silently overwrite curated facts and the app remains useful without it.

## ADR-003 — Static browser projection of SQLite

**Date:** 2026-07  
**Decision:** Keep SQLite as the authoritative graph and export a browser-readable JSON projection for the current static app.  
**Reason:** The app needs local, dependency-free lookup now while preserving a durable database model for future SQLite-WASM or server adapters.  
**Alternatives:** Browser-owned JSON as source of truth; immediate backend dependency.  
**Long-term impact:** Export compatibility is a maintained adapter boundary, not an architectural fork.

## ADR-004 — Deterministic-first Sentence Intelligence

**Date:** 2026-07  
**Decision:** Build local token/object resolution and bounded grammar detection before AI analysis.  
**Reason:** Learners need traceable, linkable analysis, and unknown content must be represented honestly.  
**Alternatives:** Free-form AI sentence explanations; sentence pages without graph references.  
**Long-term impact:** AI can enrich a stable analysis contract instead of replacing it.

## ADR-005 — Graph-native conjugation realizations

**Date:** 2026-07  
**Decision:** Model simple forms and compound/periphrastic realizations as Language Objects with ordered components; organize tenses through learning-group graph data.  
**Reason:** Conjugation is learning content, not an unstructured table, and components must remain explorable.  
**Alternatives:** Hard-coded UI tables; one giant tense dropdown; duplicate strings for compound forms.  
**Long-term impact:** Adding a tense is primarily data work and forms remain connected across pages and sentences.

## ADR-006 — Pronunciation as first-class graph knowledge

**Date:** 2026-07-17  
**Decision:** Represent pronunciation as `pronunciation` Language Objects linked by `has_pronunciation`, with structured details and a replaceable local-first playback provider chain.  
**Reason:** Lemmas and inflected forms have different pronunciations, and audio delivery must not dictate data ownership.  
**Alternatives:** Lemma IPA fallback for forms; UI-owned audio logic; cloud speech API.  
**Long-term impact:** Pronunciation is reusable across words, sentences, conjugation, and future listening features; drafts and regional variants can coexist without schema redesign.

## ADR-007 — Documentation as a production boundary

**Date:** 2026-07-17  
**Decision:** Maintain this `/docs` system as the project’s durable operating memory.  
**Reason:** Future contributors and AI agents must be able to work from explicit decisions rather than conversation history.  
**Alternatives:** README-only notes; relying on commits and chat logs.  
**Long-term impact:** Architectural review becomes repeatable across years and contributors.

## ADR-008 — Source-independent canonical identities, facts, and Learning Layer

**Date:** 2026-07-17
**Decision:** Canonical Language Objects use permanent source-independent UUID identities. Linguistic knowledge is represented as Object → Fact → Evidence, and explanations live in a general Learning Layer rather than an AI-specific layer.
**Reason:** Imports must be replaceable without breaking saved objects, APIs, or learner history; individual facts require independent provenance and conflict handling; learning material can be AI-, teacher-, human-, or source-authored without becoming canonical truth.
**Alternatives:** Importer-generated object IDs; object-level source attribution only; an AI-only enrichment table.
**Long-term impact:** The graph can evolve across sources and content authors while preserving durable identity and provenance.

## ADR-009 — Predicate facts, immutable learning revisions, and non-canonical analysis

**Date:** 2026-07-17
**Decision:** Canonical knowledge uses predicate-based typed facts with fact-level evidence and lifecycle. Learning Resources have immutable ordered revisions, with at most one published revision. Sentence parser and AI outputs remain non-canonical analysis records that may reference canonical UUIDs and Learning Resource revisions only.
**Reason:** Predicate claims make indexing and conflict handling explicit; revisions preserve teaching-content history; natural-language analysis must enrich graph navigation without redefining linguistic truth.
**Alternatives:** Anonymous property values; destructive edits to explanations; allowing parser/AI outputs to write directly to the graph.
**Long-term impact:** The future parser can support arbitrary French input and AI-assisted explanations without requiring a graph redesign or weakening provenance.

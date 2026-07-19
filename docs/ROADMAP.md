# Liens Roadmap

The roadmap is organized by product capability. It is not a promise of implementation order; each milestone must pass architecture review and approval first.

## Completed foundations

- **Language knowledge graph:** SQLite Language Objects, typed relationships, stable IDs, browser export, accent-insensitive local lookup, and A1–B2 lexical coverage.
- **Learning loop MVP:** direct object routing, back/home navigation, bilingual support with optional Chinese, typed local saves, flexible collections, and a calm Today’s Review flow backed by learner-owned IndexedDB state.
- **Sentence Intelligence:** deterministic local token resolution, grammar/expression recognition, sentence breakdown, and teacher-guidance links.
- **Verb system:** graph-native forms, pedagogical learning groups, reusable tenses, component-based realizations, and structured teaching resources.
- **Pronunciation foundation:** graph-native pronunciation objects, independent core-form IPA, local-first provider architecture, and lightweight source display.
- **Project governance:** durable documentation system and architecture decision record.
- **Experience refinement:** consistent focus, hover, active, motion, responsive, and accessibility behavior across the existing learning surfaces.
- **A1 Golden Slice:** source-backed reference implementation complete: FLELex baseline coverage, Lexique morphology and pronunciation representations, Kaikki senses/expressions/examples/lexical relations, Tex grammar topology, browser projection, and a passing provenance/integrity audit. Explicit source coverage gaps remain recorded rather than generated.

## Current milestone

**Architecture Freeze v1.0 — completed.** The browser data-package/access-adapter portion of the Data Build and Release Foundation is complete; the remaining work is a single end-to-end build and release-manifest workflow.

**C1/C2 lexical baseline — prepared.** The same hash-locked FLELex release has a reproducible C1/C2 canonical lexical-baseline manifest and importer. Its release build must remain artifact-based before browser delivery; C1/C2 senses, morphology, pronunciation, examples, expressions, and grammar follow as separate source-backed phases.

## Near-term foundation milestone

### Data Build and Release Foundation

Before expanding the graph substantially beyond A1:

- create one deterministic build command from pinned source manifests through validation, export, and audit;
- emit immutable release manifests with source checksums, schema/importer versions, artifact hashes, coverage, attribution, and compatibility information;
- treat SQLite and browser indexes as generated release artifacts rather than ordinary Git history;
- define artifact distribution and rollback before rewriting the existing branch history;
- preserve the completed browser data-package/access-adapter boundary: a lookup bootstrap plus deterministic, integrity-hashed lazy detail shards.

This foundation is specified in [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md).

## Next capability themes

### Word Graph

Improve curated definitions, examples, collocations, preposition behavior, frequency/CEFR quality, and coverage auditing without duplicating objects.

### Sentence Intelligence

Expand deterministic recognition, sentence-level explanations, error-aware confidence, and reviewed promotion of reusable constructions.

### Verb System

Populate additional paradigms and forms as data, complete tense teaching resources, and support irregularity/spelling guidance.

### Pronunciation

Add reviewed pronunciation metadata, local cached recordings or local TTS, liaison/elision learning notes, and future listening activities.

### Review and Collections

Evolve the typed-save and collection MVP into relationship-aware prompts, durable spaced-review scheduling, goals, account persistence, and sync—without flattening graph objects into generic cards.

### Reading, Listening, and Writing

Add connected reading passages, listening exercises, writing feedback objects, and learner progress without breaking the shared graph model.

### AI Enrichment

Refine structured, provenance-bound learning drafts through real teaching-quality evaluation, curated replacement, and a future review/promotion workflow.

### Publishing

Establish reproducible data builds, quality gates, licensing checks, deployment, privacy rules, backups, and release versioning.

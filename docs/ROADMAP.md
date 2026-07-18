# Liens Roadmap

The roadmap is organized by product capability. It is not a promise of implementation order; each milestone must pass architecture review and approval first.

## Completed foundations

- **Language knowledge graph:** SQLite Language Objects, typed relationships, stable IDs, browser export, accent-insensitive local lookup, and A1–B2 lexical coverage.
- **Learning surfaces:** direct object routing, back/home navigation, bilingual support with optional Chinese, local saves, and vocabulary view.
- **Sentence Intelligence:** deterministic local token resolution, grammar/expression recognition, sentence breakdown, and teacher-guidance links.
- **Verb system:** graph-native forms, pedagogical learning groups, reusable tenses, component-based realizations, and structured teaching resources.
- **Pronunciation foundation:** graph-native pronunciation objects, independent core-form IPA, local-first provider architecture, and lightweight source display.
- **Project governance:** durable documentation system and architecture decision record.
- **Experience refinement:** consistent focus, hover, active, motion, responsive, and accessibility behavior across the existing learning surfaces.
- **A1 Golden Slice:** source-backed reference implementation complete: FLELex baseline coverage, Lexique morphology and pronunciation representations, Kaikki senses/expressions/examples/lexical relations, Tex grammar topology, browser projection, and a passing provenance/integrity audit. Explicit source coverage gaps remain recorded rather than generated.

## Current milestone

**Architecture Freeze v1.0 — completed.** The browser data-package/access-adapter portion of the Data Build and Release Foundation is complete; the remaining work is a single end-to-end build and release-manifest workflow.

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

Build collection types for vocabulary, sentences, and collocations; introduce durable spaced-review state and meaningful learning actions.

### Reading, Listening, and Writing

Add connected reading passages, listening exercises, writing feedback objects, and learner progress without breaking the shared graph model.

### AI Enrichment

Introduce structured, provenance-bound draft generation only after review workflow, data contracts, and safety boundaries are designed.

### Publishing

Establish reproducible data builds, quality gates, licensing checks, deployment, privacy rules, backups, and release versioning.

# Liens Architecture & Product Manual

**Status:** Official long-term handover manual
**Audience:** Senior engineers, technical product owners, data curators, and future maintainers
**Scope:** Product intent, architecture, data ownership, operations, and development as of 2026-07-20

Liens is a French learning environment built around a connected Language Knowledge Graph. This manual explains the system as a durable product, not merely as the current static web application. It is written for a maintainer who has no access to prior conversations.

## How to use this manual

Read the chapters in this order when inheriting the project:

1. [Product and experience](manual/01-product-and-experience.md) — what Liens is, what it must not become, and how a learner should experience it.
2. [System architecture](manual/02-system-architecture.md) — layers, boundaries, data flow, and ownership.
3. [Data model and storage](manual/03-data-model-and-storage.md) — graph entities, identities, SQLite, browser package, IndexedDB, and lifecycle rules.
4. [Imports and releases](manual/04-imports-and-releases.md) — source policy, manifests, deterministic builds, validation, and exact operational commands.
5. [AI and Learning Layer](manual/05-ai-and-learning-layer.md) — provider boundary, Gemini development adapter, prompts, cache, provenance, and replacement rules.
6. [Development and feature handbook](manual/06-development-and-features.md) — repository map, implementation ownership, tests, and user-facing features.
7. [Design history and roadmap](manual/07-design-history-and-roadmap.md) — architectural evolution, rejected paths, current limitations, and next milestones.

## Normative documents

This manual is the comprehensive explanation. The following documents remain the normative record for changes:

| Document | Authority |
| --- | --- |
| [LIENS_BIBLE.md](LIENS_BIBLE.md) | Highest-level product constitution. Preserve its learner-facing intent. |
| [ARCHITECTURE_FREEZE_V1.md](ARCHITECTURE_FREEZE_V1.md) | Long-term technical boundaries and engineering gates. |
| [DECISION_LOG.md](DECISION_LOG.md) | Append-only record of consequential decisions and their rationale. |
| [CURRENT_STATE.md](CURRENT_STATE.md) | Verified snapshot of what the active branch and release currently contain. |
| [ROADMAP.md](ROADMAP.md) | Milestone sequencing. |
| [CONTRIBUTING.md](CONTRIBUTING.md) and [AI_DEVELOPMENT_PROTOCOL.md](AI_DEVELOPMENT_PROTOCOL.md) | Required development and documentation workflow. |

When this manual conflicts with a normative document, follow the normative document and update this manual in the same milestone. Do not silently reinterpret an architectural decision.

## Non-negotiable rules

1. Canonical linguistic knowledge is source-backed, attributable, and reproducible.
2. AI drafts, learner state, and browser caches are not canonical graph knowledge.
3. Canonical identity belongs to Liens, never to an import source.
4. Generated SQLite databases and browser packages are release artifacts, not hand-edited repository truth.
5. A UI feature must strengthen exploration of Language Objects rather than introduce a competing content model.
6. New imports account for every eligible source record through a mapping or explicit exclusion.
7. Before each Git commit, perform the documentation audit defined in the contribution protocol.

## Manual maintenance

Update the affected chapter when its architectural contract becomes inaccurate. Avoid duplicate prose: subsystem contracts in `docs/architecture/` contain deeper rules and should be cross-referenced from the chapter that uses them. Update `CURRENT_STATE.md` only with verified figures from a build or audit, never estimates.

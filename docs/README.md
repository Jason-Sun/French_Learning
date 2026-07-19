# Liens documentation

This directory is the durable source of truth for Liens. It records the product intent, architectural contracts, decisions, delivery plan, and current implementation state so that future contributors do not need chat history or commit archaeology to work safely.

## Start here

1. Read [LIENS_BIBLE.md](LIENS_BIBLE.md) to understand Liens' enduring product identity.
2. Read [PRODUCT_BIBLE.md](PRODUCT_BIBLE.md) to understand the active learning and experience contract.
3. Read [ARCHITECTURE_FREEZE_V1.md](ARCHITECTURE_FREEZE_V1.md) before planning a future-facing system or changing a layer boundary.
4. Read [ARCHITECTURE_BIBLE.md](ARCHITECTURE_BIBLE.md) before designing or changing a technical system.
5. Read [CURRENT_STATE.md](CURRENT_STATE.md) before beginning work in the repository.
6. Read [ROADMAP.md](ROADMAP.md) to place a proposed milestone in the larger product.
7. Read [DECISION_LOG.md](DECISION_LOG.md) before revisiting an established architectural choice.
8. Follow [CONTRIBUTING.md](CONTRIBUTING.md) and the [AI Development Protocol](AI_DEVELOPMENT_PROTOCOL.md) for the required development protocol.

## Documents and update rules

| Document | Purpose | Update when |
| --- | --- | --- |
| [Liens Bible](LIENS_BIBLE.md) | Highest-level product constitution and long-lived identity. | Liens' enduring product philosophy changes. |
| [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md) | Long-term product-system boundaries, data-build/release model, and mandatory engineering gates. | A documented architectural decision changes a frozen boundary. |
| [Architecture Bible](ARCHITECTURE_BIBLE.md) | Constitutional technical principles and system boundaries. | A durable architecture, ownership rule, or cross-system contract changes. |
| [Product Bible](PRODUCT_BIBLE.md) | Product philosophy and learner experience. | Product intent, learning flow, or interaction principles change. |
| [Roadmap](ROADMAP.md) | Logical progression of product capabilities. | A milestone starts, completes, is re-scoped, or is superseded. |
| [Current State](CURRENT_STATE.md) | Concise snapshot of the branch and implemented systems. | Every completed milestone and any meaningful limitation change. |
| [Decision Log](DECISION_LOG.md) | Append-only architectural decision record. | A consequential decision is approved. |
| [Contributing](CONTRIBUTING.md) | Required working agreement for people and AI agents. | Development standards or review protocol change. |
| [AI Development Protocol](AI_DEVELOPMENT_PROTOCOL.md) | Required workflow for AI-assisted project work. | AI development or commit-audit workflow changes. |
| [architecture/](architecture/) | Focused subsystem contracts. | The relevant subsystem’s data or interface changes. |
| [Source and Import Layer](architecture/source_imports.md) | Source-independent ingestion, mapping, and provenance rules. | An importer, release, identity, or evidence contract changes. |
| [Knowledge Lifecycle](architecture/knowledge_lifecycle.md) | Predicate facts, evidence, Learning Resource revisions, and parser boundaries. | Fact, learning-content, or analysis lifecycle changes. |
| [AI Learning Assistance](architecture/ai_learning_assistance.md) | Browser AI-draft boundary, provider contract, learner experience, and promotion requirements. | AI assistance, provider, draft, or promotion behaviour changes. |
| [Personal Learning Layer](architecture/personal_learning.md) | Learner-owned saves, collections, and review-event boundary. | Personal learning records, collection behavior, or review contract changes. |
| [Grammar Network](architecture/grammar_network.md) | First-class grammar objects, taxonomy, relationships, and sentence gateway. | Grammar-object or grammar-analysis contract changes. |

## Scope hierarchy

The Liens Bible explains **who Liens must remain**. The Product Bible explains **how that identity appears in the active learner experience**. The Architecture Freeze and Architecture Bible explain **what must remain true technically**. Subsystem documents explain **how a bounded system works**. The Current State explains **what exists now**. The Decision Log records **why a choice was made at a point in time**.

When documents disagree, preserve learner intent from the Liens Bible, then resolve the product or technical conflict through an explicit new decision rather than silently editing history.

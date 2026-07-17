# Contributing to Liens

## Required preflight

Before proposing or implementing a feature, every contributor—including an AI agent—must read:

1. [Liens Bible](LIENS_BIBLE.md)
2. [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md)
3. [Architecture Bible](ARCHITECTURE_BIBLE.md)
4. [Product Bible](PRODUCT_BIBLE.md)
5. [Roadmap](ROADMAP.md)
6. [Current State](CURRENT_STATE.md)
7. [Decision Log](DECISION_LOG.md)

Then verify that the proposal is consistent with them. If it conflicts, explain the conflict and obtain a decision before editing implementation code.

## Milestone protocol

```text
Architecture review
        ↓
Discussion and approval
        ↓
Implementation
        ↓
Testing
        ↓
Documentation update
        ↓
Architecture review
```

No major milestone is complete without its documentation update and final architecture check.

## Engineering rules

- Architecture precedes implementation.
- Prefer reusable objects, typed relationships, modular adapters, and data-driven behavior.
- Do not duplicate grammar, pronunciation, conjugation, or lexical facts in a page-specific format.
- Keep SQLite as the runtime linguistic source of truth; browser projections are adapters. The reproducible build recipe, not a checked-in database blob, is the long-term repository source of truth.
- Preserve canonical French spelling while normalizing only lookup keys.
- Protect backwards compatibility through additive migrations and explicit adapters whenever practical.
- Keep AI output structured, provenance-bound, draft by default, and unable to overwrite curated content.
- Preserve the visual identity unless a product/design decision authorizes a change.
- Do not introduce a cloud dependency for a local capability without explicit product approval.
- Update affected documentation in the same milestone.

## Data rules

- Give each durable learning concept a stable Language Object identity.
- Use typed graph edges instead of duplicating references in UI code.
- A form owns its own pronunciation; never copy or inherit its lemma’s pronunciation.
- Use source, provenance, confidence, and review status for imported or generated knowledge.
- Seed content through reviewable data files and reproducible scripts where possible.

## Testing and delivery

- Verify migrations, exports, and relevant lookup/analysis behavior.
- Test user-visible changes against the static app served over HTTP.
- Keep commits small, cohesive, and reviewable. When the product workflow requires user testing after each commit, stop after committing.
- Record limitations honestly; do not claim coverage or curation that has not been verified.

## Documentation Audit before commit

Perform a Documentation Audit before **every** Git commit. This is a targeted accuracy check, not a requirement to touch every document.

| If this changed | Update this document |
| --- | --- |
| System architecture or a cross-system contract | `ARCHITECTURE_FREEZE_V1.md`, `ARCHITECTURE_BIBLE.md`, and any affected subsystem contract |
| Significant architectural decision | Append `DECISION_LOG.md` |
| Enduring product identity | `LIENS_BIBLE.md` |
| Active product or learning philosophy | `PRODUCT_BIBLE.md` |
| Verified project status or completed milestone | `CURRENT_STATE.md` |
| Roadmap scope or sequencing | `ROADMAP.md` |
| Development or AI-agent workflow | This file and `AI_DEVELOPMENT_PROTOCOL.md` |

The commit handoff must include a short summary. For example:

```text
Documentation Audit

✓ CURRENT_STATE.md updated
✓ ROADMAP.md unchanged
✓ ARCHITECTURE_BIBLE.md unchanged
✓ DECISION_LOG.md updated
```

If all documents remain accurate, state exactly: **“No documentation updates are required for this milestone.”** Do not edit documentation merely because a commit exists.

## AI agent protocol

An AI agent must follow [AI Development Protocol](AI_DEVELOPMENT_PROTOCOL.md). It must state which architectural documents informed its work, identify conflicts before acting, avoid inventing product requirements, perform the Documentation Audit before committing, and update only the documents that became inaccurate.

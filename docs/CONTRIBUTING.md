# Contributing to Liens

## Required preflight

Before proposing or implementing a feature, every contributor—including an AI agent—must read:

1. [Architecture Bible](ARCHITECTURE_BIBLE.md)
2. [Product Bible](PRODUCT_BIBLE.md)
3. [Roadmap](ROADMAP.md)
4. [Current State](CURRENT_STATE.md)
5. [Decision Log](DECISION_LOG.md)

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
- Keep SQLite as the linguistic source of truth; browser projections are adapters.
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

## AI agent protocol

An AI agent must state which architectural documents informed its work, identify conflicts before acting, avoid inventing product requirements, and update the appropriate state/decision/subsystem documents before declaring a milestone complete.

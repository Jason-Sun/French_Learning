# Liens AI Development Protocol

This protocol governs any AI agent working on Liens. It exists to preserve product intent and architecture across conversations, models, and contributors.

## Before implementation

1. Read the Product Bible, Architecture Bible, Roadmap, Current State, and Decision Log.
2. Inspect the relevant code, data model, and current working tree.
3. State the intended scope and any architectural conflict before changing code.
4. Do not treat chat history as a source of truth when the documentation or repository provides stronger evidence.

## During implementation

- Preserve the Language Object Graph as the linguistic source of truth.
- Prefer data and typed relationships over duplicated UI logic.
- Keep AI-generated knowledge as structured, provenance-bound draft content.
- Preserve backwards compatibility and the established visual identity unless the approved task says otherwise.
- Test in proportion to the risk of the change.
- Keep work in small, reviewable commits when the project workflow requests it.

## Documentation Audit before every commit

Before creating a Git commit, audit documentation for accuracy:

1. Did the system architecture change? Update `ARCHITECTURE_BIBLE.md` and affected subsystem documentation.
2. Was a significant architectural decision made? Append `DECISION_LOG.md`.
3. Did product or learning philosophy change? Update `PRODUCT_BIBLE.md`.
4. Did verified project state or milestone change? Update `CURRENT_STATE.md`.
5. Did the roadmap change? Update `ROADMAP.md`.
6. Did the development workflow change? Update `CONTRIBUTING.md` and this protocol.

Report the result immediately before commit. If no document became inaccurate, say: **“No documentation updates are required for this milestone.”**

The audit prevents stale documentation; it does not justify mechanical edits to every file.

## Completion

Before calling a milestone complete, report what changed, how it was verified, the Documentation Audit result, the commit identifier, and any next testing step. If a user-testing gate applies, stop after the commit and wait for the result.

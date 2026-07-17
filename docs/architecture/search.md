# Search and Resolution

## Responsibility

Turn learner input into the best local learning route while preserving canonical French data.

## Contract

1. Preserve the original input for display and sentence analysis.
2. Build a normalized key by case-folding, normalizing apostrophes, and removing French diacritics for lookup only.
3. Search the exported Language Object index.
4. Prefer an exact `inflected_form` when one exists, then the relevant lemma or multi-word object.
5. Route resolved objects directly to their own object page.
6. Route unresolved multi-token input to Sentence Intelligence.
7. Present unresolved single-token input honestly; do not fabricate an AI answer.

## Guarantees

- `etre` resolves to canonical `être`; stored display text is never degraded.
- `as` resolves to its own form object, then exposes its `inflected_form_of` link to `avoir`.
- Multi-word expressions can resolve as one object before sentence analysis.

## Boundaries

The browser index is an adapter generated from SQLite. Search behavior must be implemented generically over types and relationships, never as a list of special-cased verbs.

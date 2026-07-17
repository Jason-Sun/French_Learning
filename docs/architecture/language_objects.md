# Language Object Graph

## Responsibility

Provide one stable, reusable identity for every durable learnable French element and connect those elements through typed relationships.

## Core contract

- The canonical identity registry owns permanent UUIDv5 identities. Current `language_objects.id` remains a browser-compatible runtime key during migration; external links and future learner state use `canonical_id`.
- Canonical knowledge follows **Object → Fact → Evidence**. Objects own identity, atomic facts own claims, and evidence links each claim to one or more immutable source records.
- `relationships` owns directed semantic and navigational links.
- Specialized tables own structured facts without fragmenting identity.
- The browser uses stable IDs; it may not create a second canonical representation of linguistic knowledge.

## Ownership examples

| Knowledge | Owner |
| --- | --- |
| Lemma spelling, CEFR, POS, frequency | `word` object |
| Person/mood/tense of a surface form | `inflected_form` + `form_features` |
| Pedagogical tense placement | `conjugation_tense` + learning group |
| Component sequence of a compound realization | `conjugation_realization_components` |
| IPA and pronunciation notes | `pronunciation` object + details |
| Teacher explanation | `learning_resource` + teaching guidance |

## Extension test

Before adding a table or UI state, ask: is this a new Language Object type, structured metadata on an existing object, a typed relationship, an analysis instance, or learner-specific state? Choose the smallest durable ownership boundary.

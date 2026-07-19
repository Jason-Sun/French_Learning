# Personal Learning Layer

The Personal Learning Layer stores a learner’s choices and activity. It is not part of the canonical Language Graph and it is not the AI Learning Database.

## Boundary

The canonical graph answers: “What is this French language object?”

The Personal Learning Layer answers: “What does this learner want to return to?”

It may reference a canonical UUID, but it never copies, edits, or promotes canonical facts. A learner-entered sentence may be saved with its input text and local-analysis context even if no canonical sentence exists.

## Local records

The browser MVP uses IndexedDB database `liens-personal-learning`:

| Store | Responsibility |
| --- | --- |
| `learning_objects` | A typed learner save: word, sense, form, grammar, expression, canonical sentence, or learner sentence. It has a local UUID, stable target key, optional canonical target UUID, owner/context links, title, and learning context. |
| `collections` | Learner-named groups plus the built-in `Saved` collection. |
| `collection_memberships` | Many-to-many membership: an object can appear in several collections without a copied card. |
| `review_events` | Append-only responses to a review prompt. |

Legacy `liens-saved` localStorage records are imported once by target key, so repeated launches do not duplicate saves.

## Vocabulary Notebook MVP

The Vocabulary entry point is a calm reading notebook over the existing saved
objects and collection memberships; it creates no cards, copied content, or new
database records. A learner can switch between:

- **List view** for scanning saved connections in a collection;
- **Card view** for reading one existing saved connection at a time, with
  previous/next navigation and an optional local shuffle order.

Both views can open the original Word, Form, Sentence, Grammar, or Expression
page and remove the existing learner save. Shuffle affects only the current
browser view order; it is not a review schedule, does not change collection
membership, and is not persisted as a learning claim.

## Current review contract

Today’s Review is intentionally a small learning loop, not a spaced-repetition claim. It offers each saved connection that has not been revisited today, records Again / Good / Easy as an event, and keeps the object navigable back into Liens. Prompts vary by saved type so a form reconnects to its lemma, a sense reconnects to its word, and a sentence reconnects to its local analysis.

Future scheduling may add due dates, intervals, device sync, and relationship-aware sequencing to the same learner-object identities. It must not change the graph or flatten objects into isolated flashcards.

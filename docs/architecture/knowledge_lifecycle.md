# Knowledge Lifecycle and Analysis Boundary

## Canonical fact contract

Every canonical assertion is a predicate-based claim:

```text
Language Object → predicate → typed value → one or more Evidence records
```

`canonical_facts` requires a predicate from `fact_predicates`; its value is stored in exactly one typed value table (`code`, `number`, `text`, or `object`), and `fact_evidence` ties the claim to immutable source records. The `lifecycle` belongs to the individual fact, not the whole object.

Conflicting source claims are preserved as separate facts with separate evidence. A future editorial policy may mark a claim canonical, superseded, or disputed without deleting either the object or its source history.

## Learning Resource revision contract

A Learning Resource is a stable resource object. Its explanatory content lives in immutable, ordered revisions:

```text
Learning Resource → Revision 1 → Revision 2 → Revision 3
```

Revision text cannot be updated or deleted. Create a new revision and link it to the revision it replaces. A partial unique index permits at most one `published` revision per resource; draft, reviewed, superseded, and deprecated history remains available.

Learning Resources are never canonical linguistic facts. Their authoring mode may be human, teacher, AI, or imported.

## Natural-language analysis boundary

Sentence analysis is non-canonical and is stored per input in `sentence_analysis_instances`. Future deterministic, AI-assisted, or hybrid engines write spans and graph matches to `sentence_analysis_object_matches`. A span can resolve to a lemma, inflected form, contraction component, expression, collocation, grammar construction, sentence target, or remain unresolved.

The analysis layer may reference canonical UUIDs and link a learner-facing explanation revision. It cannot promote an analysis result into canonical objects, facts, or relationships. Promotion remains an explicit, reviewed source/import workflow.

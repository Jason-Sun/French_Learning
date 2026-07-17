# Grammar Network Review Examples

These are proposed records for product review only. They are **not imported**, not source-backed, and not canonical data.

## Example 1 — Present with future meaning

```text
Sentence: Je vais au cinéma ce soir.

Candidate matches
  vais      → inflected form of aller
  Présent   → Grammar Object (conjugation_tense)
  ce soir   → time-expression object

Proposed graph path
  vais → expresses → Présent
  ce soir → illustrates → Présent
  Présent → contrasts_with → Futur proche
```

The learner-facing explanation would be a Learning Resource: the present form can describe a planned future event when context such as `ce soir` establishes future time. It must not misclassify `vais` as *futur proche* because no infinitive follows.

## Example 2 — Subjunctive trigger

```text
Sentence: Il faut que tu viennes.

Candidate matches
  il faut que          → expression object
  viennes              → inflected form of venir
  Subjonctif présent   → Grammar Object (conjugation_tense)

Proposed graph path
  il faut que → triggers_grammar → Subjonctif présent
  viennes → expresses → Subjonctif présent
  Subjonctif présent → belongs_to_grammar_topic → Verb mood
```

The learner can open the subjunctive object to explore trigger expressions, related forms, comparisons, curated examples, and revisioned explanations.

## Example 3 — Direct object pronouns

```text
Candidate Grammar Object: Direct object pronouns
Category: pronoun_system

Proposed graph path
  Direct object pronouns → requires → Personal pronouns
  Direct object pronouns → governs_agreement → Past participle agreement
  Direct object pronouns → contrasts_with → Indirect object pronouns
```

These examples show the intended graph shape only. Source-backed canonical objects, facts, relationships, and examples require the later import and editorial workflow.

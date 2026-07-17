# Conjugation System

## Responsibility

Represent verb acquisition as a connected, pedagogically ordered graph rather than a flat table.

## Data model

```text
verb
  → belongs_to_conjugation → root paradigm
  → contains → verb-specific tense paradigm
  → realizes_tense → reusable conjugation tense
  → member_of_paradigm → simple form / realization
```

Learning groups contain reusable tense objects. `conjugation_tense_metadata` carries CEFR recommendation, order, formation, usage/explanation references, source, confidence, and review status. `conjugation_realization` makes compound/periphrastic forms navigable via ordered component objects.

French verb group is a canonical predicate fact: `verb_group → first_group | second_group | third_group`. The v1 derivation policy classifies `-er` infinitives as first group except the structured `aller` exception; it uses a source-backed present participle in `-issant` to identify second-group `-ir` verbs; remaining supported cases are third group. The fact records both the policy derivation and its underlying source records. `verb_metadata` remains a compatibility adapter for auxiliary, future-stem, and legacy draft material; it is not the authority for group provenance.

Source morphology begins as individual asserted `inflected_form` analyses. The form-projection adapter deterministically maps a supported `(mood, tense)` pair to the reusable tense object, creates a verb-specific tense paradigm when necessary, and adds `root → contains → tense paradigm → realizes_tense → tense` plus `form → member_of_paradigm → tense paradigm`. Every projected edge is evidenced from its original form record; a source tense without a matching learning tense stays outside the learner selector.

## UI contract

Core learning groups are expanded by default; advanced groups are collapsed. One tense is visible at once. A verb page presents its sourced/derived French group above those controls; unsupported classifications remain visibly unavailable rather than guessed. Rows use canonical pedagogical subject order, not raw database ordering. Forms and realizations are clickable Language Objects.

## Evolution rule

Adding a tense, form, explanation, or example should be a data operation. Do not add a verb-specific branch to browser UI code.

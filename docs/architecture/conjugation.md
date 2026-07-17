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

Learning groups contain reusable tense objects. `conjugation_tense_metadata` carries CEFR recommendation, order, formation, usage/explanation references, source, confidence, and review status. `verb_metadata` owns verb group and irregularity information. `conjugation_realization` makes compound/periphrastic forms navigable via ordered component objects.

## UI contract

Core learning groups are expanded by default; advanced groups are collapsed. One tense is visible at once. Rows use canonical pedagogical subject order, not raw database ordering. Forms and realizations are clickable Language Objects.

## Evolution rule

Adding a tense, form, explanation, or example should be a data operation. Do not add a verb-specific branch to browser UI code.

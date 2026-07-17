# Grammar Network

## Responsibility

Make grammar a first-class, explorable part of the Language Graph. A sentence is an entry point that matches existing grammar objects; it never creates grammar knowledge dynamically.

## Grammar objects

Existing Language Object types remain the canonical units:

- `grammar_construction` for constructions such as negation, relative clauses, or direct-object pronouns;
- `conjugation_tense` for named tense and mood learning targets;
- `sentence_pattern` for reusable sentence-level patterns;
- `grammar_topic` for broad, non-duplicating navigational groupings.

`grammar_metadata` classifies any of these canonical UUIDs by category, pedagogical order, sentence-detection priority, and review status. It does not duplicate CEFR or explanatory content, which belong to facts and Learning Resources respectively.

## Grammar graph contract

Grammar objects use ordinary typed graph relationships. Important edges include:

- `triggers_grammar`: expression or construction → grammar object;
- `contrasts_with`: grammar object ↔ grammar object;
- `requires`: grammar object → prerequisite;
- `governs_agreement`: agreement rule → relevant object or form;
- `belongs_to_grammar_topic`: detailed object → broad grammar topic;
- existing `illustrates`, `expresses`, and `realizes_tense` edges.

Long learner-facing explanations are revisioned Learning Resources. Atomic canonical claims remain predicate facts with evidence.

## A1 source baseline

The first A1 grammar network is sourced from the frozen CC-BY Tex's French Grammar index. It covers source-indexed noun, determiner, adjective, pronoun, negation, preposition, interrogative, and tense/aspect/mood topics, with selected construction patterns and components. It is intentionally a navigational foundation, not an assertion of exhaustive French grammar coverage.

## Sentence gateway contract

Future sentence analysis records `grammar_object` matches against canonical UUIDs, alongside lemmas, inflected forms, contractions, and expressions. It retains evidence spans and confidence but cannot create canonical objects, facts, or relationships.

For example, an analysis may match `il faut que` to an expression object, `viennes` to an inflected form, and then use the existing `triggers_grammar` edge to reach the canonical `Subjonctif présent` object. AI may explain the matched graph path through a Learning Resource revision; it does not define the grammar object.

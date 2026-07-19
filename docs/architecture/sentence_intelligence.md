# Sentence Intelligence

## Responsibility

Produce a deterministic, evidence-linked local analysis of a learner sentence using the exported Language Object Graph.

## Current interface

Input: source sentence and optional saved object IDs.  
Output: tokens, resolved object/lemma IDs, form analyses, analysis nodes, typed edges, recognized expressions, grammar nodes, unknown tokens, learning candidates, provenance, confidence, and transient cache status.

## Canonical boundary

An analysis may resolve spans to canonical UUIDs through `sentence_analysis_object_matches`, including contraction components, overlapping multi-word objects, and first-class `grammar_object` matches. It remains a per-input, non-canonical record. Deterministic and future AI-assisted analysis may link a Learning Resource revision for learner-facing guidance, but cannot create or overwrite canonical Language Objects, Facts, Evidence, or relationships.

Deterministic construction recognition must test the complete structural condition before attaching a Grammar Object. For example, *futur proche* requires a present-tense inflected form of `aller` followed by an infinitive verb; a present form of `aller` followed by a destination phrase is not *futur proche*.

The learner-facing local reading must distinguish a resolved **form analysis** from a matched **Grammar Object**. A form such as `vais` may be shown as present indicative, first-person singular of `aller`; that alone does not license the UI or an AI resource to claim *futur proche*.

## Current behavior

- Tokenizes French text and handles selected contractions and elisions.
- Resolves exact local forms and lemmas.
- Emits explicit form-analysis nodes for resolved inflected forms.
- Recognizes locally modeled multi-word expressions from two to five components.
- Detects supported patterns including passé composé, futur proche, negation, reflexive constructions, and a simple subordinate-clause signal.
- Links grammar nodes to structured teacher guidance when present.

## Non-goals

It does not claim complete French parsing, create canonical knowledge automatically, or use AI to conceal uncertainty. Unknown tokens remain visible for later enrichment or learner exploration. When no Grammar Object matches, the local reading must say so rather than infer a named construction.

## Evolution rule

Add deterministic rules only when they can emit stable graph references and useful evidence. AI enrichment must consume and extend this structured result, not replace it with opaque prose.

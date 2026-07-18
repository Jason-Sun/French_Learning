# Source and Import Layer

## Responsibility

Make lexical resources interchangeable importers rather than defining the Language Graph around any one dataset.

## Pipeline

```text
source catalog → frozen release → source records → import run
      → record mapping / explicit exclusion → canonical objects and facts
      → fact evidence → browser export
```

`source_catalogs` stores provider and licence policy. `source_releases` freezes a version, artifact location, checksum, and scope. `source_records` preserves a source-native key. `import_runs` records reproducibility. Each eligible record must be mapped to a canonical object or receive an explicit exclusion reason. Canonical facts use `fact_evidence`; new canonical relationships use `relationship_evidence`.

## Identity contract

Importers do not generate object identities. They submit a source-independent identity key to the canonical identity registry, which resolves an existing canonical UUID or creates it through the core canonical workflow. A source replacement therefore maps to existing canonical IDs rather than invalidating learner data or links.

## Fact and evidence contract

Canonical facts are atomic claims with typed values. Source records support those facts through `fact_evidence`. Multiple releases may support or disagree with the same predicate without changing the object identity. Importers must not write undocumented source assumptions into canonical object fields.

## Acceptance contract

Coverage targets come from a frozen source release, never hard-coded application counts. A successful import has complete eligible-record accounting, no duplicate canonical identities, valid evidence, zero orphaned references, and reproducible run metadata.

## FLELex / Beacco lexical baseline

The production provenance import uses the official TreeTagger / Beacco TSV artifact. Its URL and SHA-256 are frozen in level-scoped manifests; the A1–B2 baseline manifest is `data/wordbank/import-manifests/flelex-beacco-tree-tagger-a1-b2.json`. The raw artifact is downloaded at import time rather than treated as Liens-authored data. The adapter maps source rows through canonical identity keys and never mints Language Object UUIDs.

Each selection is defined by the manifest’s explicit `level` or `levels` list. Its report accounts for every selected row by level as a canonical mapping or explicit exclusion, and evidences the source-supported part of speech, CEFR level, and total frequency facts independently. A multi-level import is one reproducible source release run, not a new identity system.

## Lexique 3.83 A1 morphology and pronunciation baseline

Lexique 3.83 supplies source-backed inflected surfaces, lemmas, verb features, gender, number, a Lexique-specific phonological code, and syllabification. Its phonological code is a source representation, not verified IPA.

The morphology adapters select an explicit CEFR-level scope from their manifests and import validated verb, noun, adjective, and function-word analyses. The completed A1 Golden Slice is the reference scope; the same importer contract is parameterized for A2–B2 expansion. For pronouns, articles, and possessive determiners, the adapter adds only gender/number facts asserted for an existing canonical object. Lexique does not establish paradigm links between variants such as `mon` and `ma`, so the importer never manufactures a form relationship from its rows alone.

Every Lexique-created `inflected_form_of` edge has direct row-level relationship evidence. A `member_of_paradigm` edge is a transparent graph derivation from that evidenced form link and an existing verb-paradigm link, so it retains the same source record with `evidence_role = derived_from_asserted_form`; it is never presented as a direct Lexique assertion.

The pronunciation adapter reuses the same immutable source-row identity and attaches two representations to each mapped Language Object: `phonological_code` with `transcription_system = lexique383`, and structured `syllabification`. It never exports either representation through the browser's verified-IPA projection.

Each Lexique `has_pronunciation` edge is evidenced by the same source row that evidences its representations. The graph link is therefore attributable without treating the source phonological code as IPA.

The pronunciation report accounts for every eligible source row as a mapped target or an explicit exclusion. Rows that conflict with another lexical identity or lack the features required to create a canonical form remain in `import_exclusions`; they are never silently discarded.

## Kaikki / English Wiktionary A1 sense baseline

Kaikki's French dictionary is a structured extraction from English Wiktionary. The frozen A1 sense release and its checksum live in `kaikki-enwiktionary-french-a1-senses.json`; it carries the upstream CC BY-SA/GFDL attribution obligations. It is used for English glosses, not as a CEFR classifier.

The adapter matches a source entry only when its French headword and mapped part of speech unambiguously identify an existing FLELex A1 word. Each source sense becomes a `lexical_sense` object with a source-neutral semantic key derived from its normalized English gloss set. The source-native sense ID remains solely an immutable source-record mapping. Every English gloss is an `english_gloss` fact with independent evidence; words not present in the frozen source are reported, not fabricated.

When FLELex and Kaikki classify the same French surface differently, a manifest may contain an explicit reviewed POS reconciliation. It names the source POS, target POS, and surface; the import records `mapping_kind = reviewed_pos_reconciliation`. This supplements exact source matches without changing either source representation or canonical object identity. It is a reviewable data decision, never a hidden fallback.

The `has_sense` edge is also source-evidenced from the exact source sense record. A source-backed sense therefore retains both the relationship to its word and the evidence for its English glosses independently.

The same frozen release supplies short, translated examples and explicit synonym/antonym relations. The importer accepts only extracted `example` records with an English translation and bounded sentence length. Each sentence is independent, retains a source-record alignment to the illustrated sense, and contributes an evidenced `illustrates` edge. Phrase entries are not automatically relabelled as collocations unless a future source explicitly provides that classification.

## Kaikki / English Wiktionary A1-connected expression baseline

The same hash-locked Kaikki release supplies source entries whose native part of speech is `phrase`. The expression adapter accepts a phrase only when it has an English gloss and every lexical token resolves locally to either an A1 lemma or a source-backed inflected form of an A1 lemma. This is a graph-connectivity rule, **not** a CEFR claim for the phrase itself.

Each accepted record becomes a first-class `expression` object using a source-independent surface identity. Its English translations are independently evidenced facts. Ordered components are stored in `multiword_components`, their source surfaces in `multiword_component_evidence`, and deduplicated `contains` edges carry independent relationship evidence for graph traversal. The importer does not call any Kaikki phrase an idiom or collocation: the source’s `phrase` label alone does not establish either classification.

## Tex A1 grammar baseline

Tex's French Grammar is a CC-BY educational grammar published by COERLL. Its frozen grammar-index artifact supplies a reviewed, bounded A1 topology: grammar topics, indexed constructions, and directly named components. The importer creates first-class Grammar Objects and records evidence for every new topic, component, and relationship. It does not import unbounded prose explanations as canonical facts.

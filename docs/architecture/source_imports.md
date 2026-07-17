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

## FLELex / Beacco A1 baseline

The first production provenance import uses the official TreeTagger / Beacco TSV artifact. Its URL and SHA-256 are frozen in `data/wordbank/import-manifests/flelex-beacco-tree-tagger-a1.json`; the raw artifact is downloaded at import time rather than treated as Liens-authored data. The adapter maps source rows through canonical identity keys and never mints Language Object UUIDs.

The A1 selection is defined by the release’s `level = A1` rows. Its report must account for every selected row as a canonical mapping or explicit exclusion, and must evidence the source-supported part of speech, CEFR level, and total frequency facts independently.

## Lexique 3.83 A1 morphology and pronunciation baseline

Lexique 3.83 supplies source-backed inflected surfaces, lemmas, verb features, gender, number, a Lexique-specific phonological code, and syllabification. Its phonological code is a source representation, not verified IPA.

The morphology adapters import validated A1 verb, noun, adjective, and function-word analyses. For pronouns, articles, and possessive determiners, the adapter adds only gender/number facts asserted for an existing canonical object. Lexique does not establish paradigm links between variants such as `mon` and `ma`, so the importer never manufactures a form relationship from its rows alone.

The pronunciation adapter reuses the same immutable source-row identity and attaches two representations to each mapped Language Object: `phonological_code` with `transcription_system = lexique383`, and structured `syllabification`. It never exports either representation through the browser's verified-IPA projection.

The pronunciation report accounts for every eligible source row as a mapped target or an explicit exclusion. Rows that conflict with another lexical identity or lack the features required to create a canonical form remain in `import_exclusions`; they are never silently discarded.

## Kaikki / English Wiktionary A1 sense baseline

Kaikki's French dictionary is a structured extraction from English Wiktionary. The frozen A1 sense release and its checksum live in `kaikki-enwiktionary-french-a1-senses.json`; it carries the upstream CC BY-SA/GFDL attribution obligations. It is used for English glosses, not as a CEFR classifier.

The adapter matches a source entry only when its French headword and mapped part of speech unambiguously identify an existing FLELex A1 word. Each source sense becomes a `lexical_sense` object with a source-neutral semantic key derived from its normalized English gloss set. The source-native sense ID remains solely an immutable source-record mapping. Every English gloss is an `english_gloss` fact with independent evidence; words not present in the frozen source are reported, not fabricated.

## Tex A1 grammar baseline

Tex's French Grammar is a CC-BY educational grammar published by COERLL. Its frozen grammar-index artifact supplies a reviewed, bounded A1 topology: grammar topics, indexed constructions, and directly named components. The importer creates first-class Grammar Objects and records evidence for every new topic, component, and relationship. It does not import unbounded prose explanations as canonical facts.

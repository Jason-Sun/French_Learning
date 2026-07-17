# Source and Import Layer

## Responsibility

Make lexical resources interchangeable importers rather than defining the Language Graph around any one dataset.

## Pipeline

```text
source catalog → frozen release → source records → import run
      → record mapping / explicit exclusion → canonical objects and facts
      → fact evidence → browser export
```

`source_catalogs` stores provider and licence policy. `source_releases` freezes a version, artifact location, checksum, and scope. `source_records` preserves a source-native key. `import_runs` records reproducibility. Each eligible record must be mapped to a canonical object or receive an explicit exclusion reason.

## Identity contract

Importers do not generate object identities. They submit a source-independent identity key to the canonical identity registry, which resolves an existing canonical UUID or creates it through the core canonical workflow. A source replacement therefore maps to existing canonical IDs rather than invalidating learner data or links.

## Fact and evidence contract

Canonical facts are atomic claims with typed values. Source records support those facts through `fact_evidence`. Multiple releases may support or disagree with the same predicate without changing the object identity. Importers must not write undocumented source assumptions into canonical object fields.

## Acceptance contract

Coverage targets come from a frozen source release, never hard-coded application counts. A successful import has complete eligible-record accounting, no duplicate canonical identities, valid evidence, zero orphaned references, and reproducible run metadata.

#!/usr/bin/env python3
"""Build a validated, artifact-only C1/C2 Liens graph release.

The repository contains the reproducible recipe. This command creates the
SQLite graph, browser package, reports, and release manifest in a new output
directory, without changing the development database or browser package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data" / "wordbank" / "import-manifests"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def load_manifest(name: str) -> dict:
    return json.loads((MANIFEST_DIR / name).read_text(encoding="utf-8"))


def run(script: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *arguments], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-database", type=Path, required=True, help="Verified A1–B2 graph database.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New, empty directory for this release.")
    parser.add_argument("--flelex-source", type=Path, required=True)
    parser.add_argument("--kaikki-source", type=Path, required=True)
    parser.add_argument("--lexique-source", type=Path, required=True)
    parser.add_argument("--morphalou-source", type=Path, required=True, help="Pinned Morphalou3.1 CSV ZIP archive")
    parser.add_argument("--build-id", default="liens-c1-c2-source-release-v1")
    args = parser.parse_args()

    if not args.base_database.is_file():
        raise ValueError(f"Base database does not exist: {args.base_database}")
    if args.output_dir.exists():
        raise ValueError(f"Release output directory already exists: {args.output_dir}")

    output = args.output_dir
    reports = output / "reports"
    browser = output / "browser"
    output.mkdir(parents=True)
    reports.mkdir()
    database = output / "liens-knowledge.sqlite"
    shutil.copy2(args.base_database, database)

    flelex = load_manifest("flelex-beacco-tree-tagger-c1-c2.json")
    kaikki_senses = load_manifest("kaikki-enwiktionary-french-c1-c2-senses.json")
    lexique_morphology = load_manifest("lexique383-c1-c2-morphology.json")
    lexique_pronunciation = load_manifest("lexique383-c1-c2-pronunciation.json")
    morphalou_morphology = load_manifest("morphalou31-a1-c2-morphology.json")
    kaikki_connections = load_manifest("kaikki-enwiktionary-french-c1-c2-connections.json")
    kaikki_expressions = load_manifest("kaikki-enwiktionary-french-c1-c2-expressions.json")

    run("import_flelex_lexical_baseline.py", "--database", str(database), "--source", str(args.flelex_source), "--manifest", str(MANIFEST_DIR / "flelex-beacco-tree-tagger-c1-c2.json"), "--report", str(reports / "flelex-baseline.json"))
    run("audit_cefr_lexical_baseline.py", "--database", str(database), "--source", str(args.flelex_source), "--manifest", str(MANIFEST_DIR / "flelex-beacco-tree-tagger-c1-c2.json"), "--report", str(reports / "flelex-baseline-audit.json"))
    run("import_kaikki_a1_senses.py", "--database", str(database), "--source", str(args.kaikki_source), "--manifest", str(MANIFEST_DIR / "kaikki-enwiktionary-french-c1-c2-senses.json"), "--report", str(reports / "kaikki-senses.json"))
    run("import_lexique_a1_morphology.py", "--database", str(database), "--source", str(args.lexique_source), "--manifest", str(MANIFEST_DIR / "lexique383-c1-c2-morphology.json"), "--report", str(reports / "lexique-morphology.json"))
    run("import_lexique_a1_pronunciation.py", "--database", str(database), "--source", str(args.lexique_source), "--manifest", str(MANIFEST_DIR / "lexique383-c1-c2-pronunciation.json"), "--report", str(reports / "lexique-pronunciation.json"))
    run("import_morphalou_morphology.py", "--database", str(database), "--source", str(args.morphalou_source), "--manifest", str(MANIFEST_DIR / "morphalou31-a1-c2-morphology.json"), "--report", str(reports / "morphalou-morphology.json"))
    run("import_kaikki_a1_connections.py", "--database", str(database), "--source", str(args.kaikki_source), "--manifest", str(MANIFEST_DIR / "kaikki-enwiktionary-french-c1-c2-connections.json"), "--report", str(reports / "kaikki-connections.json"))
    run("import_kaikki_a1_expressions.py", "--database", str(database), "--source", str(args.kaikki_source), "--manifest", str(MANIFEST_DIR / "kaikki-enwiktionary-french-c1-c2-expressions.json"), "--report", str(reports / "kaikki-expressions.json"))
    run("seed_conjugation_learning_catalog.py", "--database", str(database), "--catalog", str(ROOT / "data" / "wordbank" / "conjugation-paradigm-catalog.json"))
    run("derive_verb_groups.py", "--database", str(database), "--policy", str(ROOT / "data" / "wordbank" / "verb-group-policy.json"), "--report", str(reports / "verb-groups.json"))
    run("project_lexique_forms_to_tense_paradigms.py", "--database", str(database), "--report", str(reports / "tense-paradigm-projection.json"))
    run("audit_a1_b2_graph.py", "--database", str(database), "--output", str(reports / "c1-c2-graph-audit.json"), "--levels", "C1", "C2")
    run("export_wordbank_index.py", "--source", str(database), "--output-dir", str(browser))
    run("test_browser_graph_package.py", "--package-dir", str(browser))

    with sqlite3.connect(database) as connection:
        schema_version = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
    release_manifest = {
        "build_id": args.build_id,
        "built_at": datetime.now(UTC).isoformat(),
        "scope": {"cefr_levels": ["A1", "A2", "B1", "B2", "C1", "C2"]},
        "base_database": artifact(args.base_database, args.base_database.parent),
        "schema_version": schema_version[0] if schema_version else None,
        "source_releases": [
            flelex["release"],
            kaikki_senses["release"],
            lexique_morphology["release"],
            morphalou_morphology["release"],
        ],
        "input_artifacts": {
            "flelex": artifact(args.flelex_source, args.flelex_source.parent),
            "kaikki": artifact(args.kaikki_source, args.kaikki_source.parent),
            "lexique": artifact(args.lexique_source, args.lexique_source.parent),
            "morphalou": artifact(args.morphalou_source, args.morphalou_source.parent),
        },
        "import_manifests": [
            "flelex-beacco-tree-tagger-c1-c2.json",
            "kaikki-enwiktionary-french-c1-c2-senses.json",
            "lexique383-c1-c2-morphology.json",
            "lexique383-c1-c2-pronunciation.json",
            "morphalou31-a1-c2-morphology.json",
            "kaikki-enwiktionary-french-c1-c2-connections.json",
            "kaikki-enwiktionary-french-c1-c2-expressions.json",
        ],
        "artifacts": [artifact(database, output), artifact(browser / "manifest.json", output), artifact(browser / "lookup.json", output)],
        "reports": [artifact(path, output) for path in sorted(reports.glob("*.json"))],
    }
    (output / "release-manifest.json").write_text(json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built C1/C2 release {args.build_id} at {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate the generated Liens browser graph package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def shard_for(object_id: str) -> str:
    return f"{int(hashlib.sha256(object_id.encode()).hexdigest()[:8], 16) % 64:02d}"


def read_checked(root: Path, relative_path: str, metadata: dict) -> dict:
    path = root / relative_path
    payload = path.read_bytes()
    assert len(payload) == metadata["bytes"], f"Unexpected byte size: {relative_path}"
    assert hashlib.sha256(payload).hexdigest() == metadata["sha256"], (
        f"Checksum mismatch: {relative_path}"
    )
    return json.loads(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.package_dir
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["package_version"] == 1
    lookup = read_checked(root, manifest["lookup"]["path"], manifest["lookup"])
    lookup_objects = lookup["objects"]
    lookup_ids = {object_["id"] for object_ in lookup_objects}
    assert len(lookup_ids) == len(lookup_objects), "Duplicate lookup object identity"

    detail_ids: set[str] = set()
    for shard, metadata in manifest["object_shards"].items():
        payload = read_checked(root, metadata["path"], metadata)
        objects = payload["objects"]
        assert len(objects) == metadata["object_count"], f"Wrong object count: {shard}"
        for object_ in objects:
            assert object_["id"] not in detail_ids, f"Duplicate detail object: {object_['id']}"
            assert shard_for(object_["id"]) == shard, f"Wrong deterministic shard: {object_['id']}"
            detail_ids.add(object_["id"])

    assert lookup_ids <= detail_ids, "Lookup object without detail projection"
    for object_ in lookup_objects:
        assert object_["detail_shard"] in manifest["object_shards"], (
            f"Missing lookup shard: {object_['id']}"
        )
        assert object_["detail_shard"] == shard_for(object_["id"]), (
            f"Lookup shard mismatch: {object_['id']}"
        )

    assert len(lookup_objects) == manifest["counts"]["lookup_objects"]
    assert len(detail_ids) == manifest["counts"]["detail_objects"]
    print(
        "Browser graph package checks passed: "
        f"{len(lookup_objects)} lookup objects, {len(detail_ids)} detail objects, "
        f"{len(manifest['object_shards'])} shards."
    )


if __name__ == "__main__":
    main()

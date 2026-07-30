#!/usr/bin/env python3
"""Build the generated registry index from packages.txt.

Walks every URL in packages.txt, fetches each repo's mpy-registry.yaml, and
writes:
  - dist/index.json            - all packages
  - dist/categories/<cat>.json - packages in that category

A single package's repo being unreachable or invalid does NOT fail the
build - it's skipped with a warning. A rebuild for the whole registry
should never be blocked by one unrelated package going stale, same
reasoning as validate_packages.py only checking newly added entries.
"""
import argparse
import json
import sys
from collections import defaultdict

import jsonschema

from registry_lib import ManifestError, fetch_manifest, read_urls


def build(packages_txt, schema, token):
    packages = []
    skipped = []

    for url in read_urls(packages_txt):
        try:
            manifest = fetch_manifest(url, token)
        except ManifestError as e:
            skipped.append(f"{url}: {e}")
            continue

        try:
            jsonschema.validate(manifest, schema)
        except jsonschema.ValidationError as e:
            skipped.append(f"{url}: schema validation failed: {e.message}")
            continue

        manifest["repo_url"] = url
        packages.append(manifest)
        print(f"OK  {url} -> {manifest['name']}@{manifest['version']}")

    packages.sort(key=lambda p: p["name"])
    return packages, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", required=True, help="path to packages.txt")
    parser.add_argument("--schema", required=True, help="path to schema.json")
    parser.add_argument("--out", required=True, help="output directory (e.g. dist)")
    parser.add_argument("--github-token", default=None, help="GITHUB_TOKEN for API rate limits")
    args = parser.parse_args()

    schema = json.load(open(args.schema))
    packages, skipped = build(args.packages, schema, args.github_token)

    out_dir = args.out
    import os
    os.makedirs(os.path.join(out_dir, "categories"), exist_ok=True)

    with open(os.path.join(out_dir, "index.json"), "w") as f:
        json.dump({"packages": packages}, f, indent=2)
        f.write("\n")

    by_category = defaultdict(list)
    for p in packages:
        by_category[p["category"]].append(p)

    for category in schema["properties"]["category"]["enum"]:
        with open(os.path.join(out_dir, "categories", f"{category}.json"), "w") as f:
            json.dump({"packages": by_category.get(category, [])}, f, indent=2)
            f.write("\n")

    print(f"\nIndexed {len(packages)} package(s), skipped {len(skipped)}.")
    if skipped:
        print("Skipped:")
        for s in skipped:
            print(f"  - {s}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

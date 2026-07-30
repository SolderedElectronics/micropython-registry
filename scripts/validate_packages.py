#!/usr/bin/env python3
"""Validate newly added entries in packages.txt for a PR.

Only lines ADDED relative to the PR's base ref are checked — an
already-merged package's manifest going stale/unreachable must never block
someone else's unrelated PR.

For each added repo URL:
  - confirm it's a github.com repo and it exists
  - fetch mpy-registry.yaml from its default branch, root only
  - validate it against schema.json
  - collect its `name` for a collision check against the other newly added
    entries in this same PR (NOT against the full existing registry yet —
    that needs Phase 3's generated index to do cheaply)

Exits non-zero if any added entry fails.
"""
import argparse
import json
import sys

import jsonschema

from registry_lib import ManifestError, fetch_manifest, read_urls


def validate_added_url(url, schema, token, errors, names):
    try:
        manifest = fetch_manifest(url, token)
    except ManifestError as e:
        errors.append(f"{url}: {e}")
        return

    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{url}: schema validation failed at {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
        return

    name = manifest["name"]
    names.setdefault(name, []).append(url)
    print(f"OK  {url} -> {name}@{manifest['version']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, help="packages.txt at the PR base ref")
    parser.add_argument("--new", required=True, help="packages.txt at the PR head")
    parser.add_argument("--schema", required=True, help="path to schema.json")
    parser.add_argument("--github-token", default=None, help="GITHUB_TOKEN for API rate limits")
    args = parser.parse_args()

    schema = json.load(open(args.schema))
    old_urls = set(read_urls(args.old))
    new_urls = read_urls(args.new)

    added = [u for u in new_urls if u not in old_urls]
    removed = old_urls - set(new_urls)

    if removed:
        print(f"Note: {len(removed)} entrie(s) removed, not validated: {sorted(removed)}")

    if not added:
        print("No new packages.txt entries in this PR — nothing to validate.")
        return 0

    errors = []
    names = {}
    for url in added:
        validate_added_url(url, schema, args.github_token, errors, names)

    for name, urls in names.items():
        if len(urls) > 1:
            errors.append(f"name collision: '{name}' claimed by multiple new entries in this PR: {urls}")

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"\nAll {len(added)} new package(s) validated OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

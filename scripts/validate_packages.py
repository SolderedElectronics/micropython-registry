#!/usr/bin/env python3
"""Validate newly added entries in packages.txt for a PR.

Only lines ADDED relative to the PR's base ref are checked - an
already-merged package's manifest going stale/unreachable must never block
someone else's unrelated PR.

For each added repo URL:
  - confirm it's a github.com repo and it exists
  - fetch mpy-registry.yaml from its default branch, root only
  - validate it against schema.json
  - collect its `name` for a collision check against both the other newly
    added entries in this same PR AND every name already in the generated
    index (dist/index.json on the dist branch) - cheap now that Phase 3
    exists, since it's one fetch instead of re-fetching every existing repo

Exits non-zero if any added entry fails.
"""
import argparse
import json
import sys
import urllib.error

import jsonschema

from registry_lib import ManifestError, fetch_manifest, fetch_raw, read_urls


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


def fetch_existing_names(index_url):
    """Returns {name: repo_url} from the generated index, or raises RuntimeError."""
    try:
        raw = fetch_raw(index_url)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(str(e.reason))

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"not valid JSON ({e})")

    return {p["name"]: p.get("repo_url", "?") for p in data["packages"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, help="packages.txt at the PR base ref")
    parser.add_argument("--new", required=True, help="packages.txt at the PR head")
    parser.add_argument("--schema", required=True, help="path to schema.json")
    parser.add_argument("--github-token", default=None, help="GITHUB_TOKEN for API rate limits")
    parser.add_argument(
        "--index-url",
        default="https://raw.githubusercontent.com/SolderedElectronics/micropython-registry/dist/index.json",
        help="URL of the generated index, used for the full-registry name collision check",
    )
    args = parser.parse_args()

    schema = json.load(open(args.schema))
    old_urls = set(read_urls(args.old))
    new_urls = read_urls(args.new)

    added = [u for u in new_urls if u not in old_urls]
    removed = old_urls - set(new_urls)

    if removed:
        print(f"Note: {len(removed)} entrie(s) removed, not validated: {sorted(removed)}")

    if not added:
        print("No new packages.txt entries in this PR - nothing to validate.")
        return 0

    errors = []
    names = {}
    for url in added:
        validate_added_url(url, schema, args.github_token, errors, names)

    for name, urls in names.items():
        if len(urls) > 1:
            errors.append(f"name collision: '{name}' claimed by multiple new entries in this PR: {urls}")

    try:
        existing_names = fetch_existing_names(args.index_url)
        for name, urls in names.items():
            if name in existing_names:
                errors.append(
                    f"name collision: '{name}' already registered by {existing_names[name]}, "
                    f"claimed again by {urls}"
                )
    except RuntimeError as e:
        errors.append(f"could not fetch existing index for collision check ({args.index_url}): {e}")

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"\nAll {len(added)} new package(s) validated OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

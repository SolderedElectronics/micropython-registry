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
import re
import sys
import urllib.error
import urllib.request

import jsonschema
import yaml

GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)/?$"
)


def read_urls(path):
    urls = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def github_api_get(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def fetch_raw(url):
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.read()


def validate_added_url(url, schema, token, errors, names):
    match = GITHUB_REPO_RE.match(url)
    if not match:
        errors.append(f"{url}: not a github.com repo URL (only github.com/<owner>/<repo> supported)")
        return

    owner, repo = match.group("owner"), match.group("repo")

    try:
        meta = github_api_get(f"https://api.github.com/repos/{owner}/{repo}", token)
    except urllib.error.HTTPError as e:
        errors.append(f"{url}: repo lookup failed ({e.code} {e.reason})")
        return
    except urllib.error.URLError as e:
        errors.append(f"{url}: repo lookup failed ({e.reason})")
        return

    default_branch = meta.get("default_branch", "main")
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/mpy-registry.yaml"

    try:
        raw = fetch_raw(raw_url)
    except urllib.error.HTTPError as e:
        errors.append(f"{url}: mpy-registry.yaml not found at repo root ({e.code} {e.reason})")
        return
    except urllib.error.URLError as e:
        errors.append(f"{url}: failed to fetch mpy-registry.yaml ({e.reason})")
        return

    try:
        manifest = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        errors.append(f"{url}: mpy-registry.yaml is not valid YAML ({e})")
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

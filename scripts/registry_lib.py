"""Shared helpers for reading packages.txt and fetching mpy-registry.yaml.

Used by both validate_packages.py (PR-time validation) and build_index.py
(post-merge index generation) so the two never drift on how a manifest is
located and fetched.
"""
import json
import re
import urllib.error
import urllib.request

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


class ManifestError(Exception):
    """A repo URL couldn't be resolved to a valid manifest. .args[0] is the reason."""


def fetch_manifest(url, token):
    """Fetch and parse (but not schema-validate) the mpy-registry.yaml for a repo URL.

    Returns the parsed manifest dict, or raises ManifestError with a
    human-readable reason.
    """
    match = GITHUB_REPO_RE.match(url)
    if not match:
        raise ManifestError("not a github.com repo URL (only github.com/<owner>/<repo> supported)")

    owner, repo = match.group("owner"), match.group("repo")

    try:
        meta = github_api_get(f"https://api.github.com/repos/{owner}/{repo}", token)
    except urllib.error.HTTPError as e:
        raise ManifestError(f"repo lookup failed ({e.code} {e.reason})")
    except urllib.error.URLError as e:
        raise ManifestError(f"repo lookup failed ({e.reason})")

    default_branch = meta.get("default_branch", "main")
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/mpy-registry.yaml"

    try:
        raw = fetch_raw(raw_url)
    except urllib.error.HTTPError as e:
        raise ManifestError(f"mpy-registry.yaml not found at repo root ({e.code} {e.reason})")
    except urllib.error.URLError as e:
        raise ManifestError(f"failed to fetch mpy-registry.yaml ({e.reason})")

    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ManifestError(f"mpy-registry.yaml is not valid YAML ({e})")

// mip index-protocol translation layer.
//
// Implements the query shape mip itself expects (verified against
// micropython-lib's actual mip source, not just docs): a GET to
//   /package/<mpy_version>/<name>/<version>.json
// must return the same {urls, deps, version} shape as a package's own mip
// package.json - because that IS what mip expects; a custom index isn't a
// different format, just a different place to fetch that same shape from,
// keyed by registry package name instead of a github: URL.
//
// One correctness landmine, found by reading mip's source directly: when a
// caller does mip.install("name") with NO version pinned, mip defaults
// version="latest" and then uses that literal string as the git branch/tag
// when resolving any "github:org/repo/path" shorthand inside the returned
// urls list. None of our package repos have a branch called "latest", so
// proxying an author's package.json verbatim would silently 404 on every
// unpinned install (the common case). Fix: resolve github: shorthand into
// fully-qualified https://raw.githubusercontent.com/.../HEAD/... URLs
// ourselves before returning - mip passes plain https:// URLs through
// unmodified, sidestepping the whole version-as-branch substitution.
//
// This intentionally does NOT support the "hashes" field (content-addressed
// storage keyed by sha256, e.g. micropython.org/pi/v2's own CDN) - packages
// here stay hosted in their own repos, so only "urls" is needed.
//
// Version pinning is NOT supported: only "latest" (or the current version
// string, which is treated identically) is served, since the registry only
// tracks each package's current state, not historical releases.

const INDEX_JSON_URL =
  "https://raw.githubusercontent.com/SolderedElectronics/micropython-registry/dist/index.json";

const GITHUB_REPO_RE = /^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+?)\/?$/;

const PACKAGE_PATH_RE = /^\/package\/([^/]+)\/([^/]+)\/([^/]+)\.json$/;

function resolveGithubShorthand(url) {
  if (!url.startsWith("github:")) return url;
  const parts = url.slice("github:".length).split("/");
  const [org, repo, ...pathParts] = parts;
  return `https://raw.githubusercontent.com/${org}/${repo}/HEAD/${pathParts.join("/")}`;
}

async function fetchIndex() {
  const resp = await fetch(INDEX_JSON_URL, {
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!resp.ok) return null;
  return resp.json();
}

async function handlePackageRequest(name, version) {
  const index = await fetchIndex();
  if (!index) {
    return new Response("Registry index unavailable", { status: 502 });
  }

  const pkg = index.packages.find((p) => p.name === name);
  if (!pkg) {
    return new Response("Package not found", { status: 404 });
  }

  if (version !== "latest" && version !== pkg.version) {
    return new Response("Version not found (only latest is served)", { status: 404 });
  }

  const repoMatch = pkg.repo_url && pkg.repo_url.match(GITHUB_REPO_RE);
  if (!repoMatch) {
    return new Response("Package repo_url missing or unsupported", { status: 500 });
  }
  const [, owner, repo] = repoMatch;
  const installPath = pkg.install_path ? `${pkg.install_path}/` : "";
  const packageJsonUrl = `https://raw.githubusercontent.com/${owner}/${repo}/HEAD/${installPath}package.json`;

  const pkgJsonResp = await fetch(packageJsonUrl);
  if (!pkgJsonResp.ok) {
    return new Response("package.json not found in package's repo", { status: 404 });
  }

  let pkgJson;
  try {
    pkgJson = await pkgJsonResp.json();
  } catch (e) {
    return new Response("package.json in package's repo is not valid JSON", { status: 502 });
  }

  if (Array.isArray(pkgJson.urls)) {
    pkgJson.urls = pkgJson.urls.map(([path, url]) => [path, resolveGithubShorthand(url)]);
  }

  return new Response(JSON.stringify(pkgJson), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

export default {
  async fetch(request) {
    if (request.method !== "GET") {
      return new Response("Method not allowed", { status: 405 });
    }

    const url = new URL(request.url);

    if (url.pathname === "/" || url.pathname === "") {
      return new Response(
        "MicroPython Registry mip index. See https://github.com/SolderedElectronics/micropython-registry\n",
        { status: 200 }
      );
    }

    const match = url.pathname.match(PACKAGE_PATH_RE);
    if (!match) {
      return new Response("Not found", { status: 404 });
    }
    const [, , name, version] = match;

    return handlePackageRequest(name, version);
  },
};

# Package Manifest Schema

Arduino Library Manager-style split, on purpose: this repo stays a thin,
flat list — no per-package files piling up here.

- **`packages.txt`** (this repo) — one package repo URL per line. That's it.
- **`mpy-registry.yaml`** (in the *package author's own repo*, always at
  repo root) — the actual metadata: name, version, description, category,
  compatibility, etc. Fetched from the author's repo at index-build time,
  not stored here.

This means updating a package's description/version/category never requires
a PR to this repo — the author just edits their own `mpy-registry.yaml` and
it's picked up on the next index build. This repo's git history therefore
only tracks *which repos are listed*, not their metadata content — see the
trust note below.

Machine-readable definition: [`schema.json`](schema.json) (JSON Schema draft
2020-12), validates `mpy-registry.yaml`.

Example: [`examples/mpy-registry.yaml`](examples/mpy-registry.yaml) — copy
this into your own repo's root, don't add it here.

## Fields (`mpy-registry.yaml`)

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | yes | string | Unique registry name. Lowercase kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`). Becomes the short-name for `--index` installs in Phase 6. CI (Phase 2) rejects a submission if the name collides with an existing package. |
| `version` | yes | string | Semver (`MAJOR.MINOR.PATCH`, optional pre-release/build metadata). |
| `description` | yes | string | One line, ≤200 chars. |
| `author` | yes | string \| object | Plain name, or `{name, email?, url?}`. |
| `license` | yes | string | SPDX identifier (`MIT`, `Apache-2.0`, `GPL-3.0-or-later`, ...). |
| `category` | yes | enum | One of: `sensors`, `displays`, `networking`, `protocols`, `audio`, `storage`, `motors-actuators`, `utilities`, `misc`. |
| `repo_url` | no | string (URI) | Self-reference only — cross-check that this manifest wasn't copy-pasted from another package without updating it. Not used to locate the package; `packages.txt` already does that. |
| `homepage` | no | string (URI) | Docs/homepage, if different from the repo itself. |
| `install_path` | no | string | Subdirectory (within this same repo) holding the installable package, for monorepo-style repos. Only affects where the package code is; `mpy-registry.yaml` itself is always read from repo root. Omit if the package is at repo root. |
| `tags` | no | string[] | Free-form search tags, beyond the fixed category. |
| `compatible_ports` | no | enum[] | `esp32`, `esp8266`, `rp2`, `samd`, `stm32`, `nrf`, `mimxrt`, `renesas-ra`, `cc3200`, `zephyr`, `unix`, `windows`, `webassembly`, `other`. Omitting means "untested", not "incompatible". |
| `compatible_boards` | no | string[] | Specific boards tested, free-form. |
| `min_micropython_version` | no | string | e.g. `1.22.0`. |
| `dependencies` | no | object[] | Other **registry** package names: `{name, version?}`. `version` is a constraint (`^1.2.0`, `>=1.0.0`); omit for "latest". |

`additionalProperties` is `false` — unknown fields fail validation rather than
being silently ignored.

## Trust note

Two layers here, worth keeping separate in your head:

1. **No human ever reviews a submission.** CI validates shape (schema) and
   reachability (repo exists, `mpy-registry.yaml` fetches, name isn't taken)
   and merges automatically on success. Nobody reads the linked repo's code
   before it enters `packages.txt`. Passing CI is not a safety or quality
   signal — only a well-formedness one.
2. **After merge**, the author can change their `mpy-registry.yaml` — or the
   package code itself — at any time, with no further PR to this repo. The
   generated index reflects whatever's in their repo at build time. Entering
   the registry once is not an ongoing guarantee about content.

On top of that, the general point still applies: `mip.install(...)` fetches
and executes third-party code on-device. Schema validation checks shape, not
safety. Verify a package's source before installing it.

## Submitting a package

1. Add `mpy-registry.yaml` to the root of **your own** package repo (copy
   [`examples/mpy-registry.yaml`](examples/mpy-registry.yaml) as a starting
   point). GitHub repos only for now — GitLab/other hosts aren't supported
   by CI yet.
2. Open a PR against **this** repo adding one or more new lines to
   `packages.txt` (your repo's URL(s), alphabetically sorted). Don't add
   any other files here.
3. CI ([`.github/workflows/validate-package.yml`](.github/workflows/validate-package.yml))
   fetches `mpy-registry.yaml` from each newly added repo, validates it
   against `schema.json`, and checks for name collisions both among the
   newly added packages and against every name already in the generated
   index ([`dist/index.json`](https://github.com/SolderedElectronics/micropython-registry/blob/dist/index.json)).
4. If validation passes, the PR **merges automatically** — there is no
   human review step. See the trust note above.

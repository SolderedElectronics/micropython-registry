# MicroPython Package Registry

A vendor-neutral, searchable index for MicroPython packages that live
scattered across individual GitHub repos — comparable to the Arduino
Library Manager or the ESP-IDF Component Registry, but with packages
staying hosted in their own repos rather than uploaded anywhere new.

## How it works

Arduino Library Manager-style split, on purpose — this repo stays a thin,
flat list, not hundreds of per-package files:

- **[`packages.txt`](packages.txt)** — the entire registry. One package
  repo URL per line.
- **`mpy-registry.yaml`** — lives in each *package author's own repo* (repo
  root), not here. Holds the real metadata: name, version, description,
  category, compatible ports, dependencies. See
  [`schema.json`](schema.json) / [`SCHEMA.md`](SCHEMA.md) for the full spec
  and [`examples/mpy-registry.yaml`](examples/mpy-registry.yaml) for a
  worked example.

Because metadata lives in the author's own repo, updating a package's
version/description never requires a PR here — CI picks up whatever's
currently in the author's repo at index-build time.

## Submitting a package

See [`SCHEMA.md`](SCHEMA.md#submitting-a-package) for the full steps. Short
version: add `mpy-registry.yaml` to your repo's root, open a PR here adding
your repo's URL to `packages.txt`.

PRs are validated automatically
([`.github/workflows/validate-package.yml`](.github/workflows/validate-package.yml)):
schema-checks your `mpy-registry.yaml`, confirms the repo resolves, checks
for name collisions against other packages in the same PR. **Passing PRs
merge automatically — there is no human review step.** CI checks shape and
reachability, not whether the linked code is safe; see the trust note in
[`SCHEMA.md`](SCHEMA.md#trust-note) before installing anything from here.

## Status

Early build-out, not yet launched. Current progress against the project
plan:

- [x] Phase 1 — manifest schema (`schema.json`, `SCHEMA.md`)
- [x] Phase 2 — CI validation + auto-merge
- [ ] Phase 3 — index generation (`dist/index.json`)
- [ ] Phase 4 — discovery website
- [ ] Phase 5 — launch / seed content
- [ ] Phase 6 — custom mip index (optional, later)

## License

MIT.

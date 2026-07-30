# MicroPython Package Registry

A vendor-neutral, searchable index for MicroPython packages that live
scattered across individual GitHub repos — comparable to the Arduino
Library Manager or the ESP-IDF Component Registry, but with packages
staying hosted in their own repos rather than uploaded anywhere new.

No accounts, nothing extra to install, no special client. If you already
use [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html)
or `mip`, you already have everything you need.

## Installing a package

Every package here stays hosted in its own GitHub repo, so you install it
the same way you'd install any `mip`-compatible package directly from
GitHub — no `--index` flag needed today:

```sh
mpremote mip install github:SolderedElectronics/Soldered-MicroPython-INA219
```

or from the device's own REPL:

```python
import mip
mip.install("github:SolderedElectronics/Soldered-MicroPython-INA219")
```

**Finding a package:** there's no browsable website yet (that's Phase 4,
not built). For now, browse the generated index directly:
[`index.json`](https://github.com/SolderedElectronics/micropython-registry/blob/dist/index.json)
(all packages) or
[`categories/`](https://github.com/SolderedElectronics/micropython-registry/tree/dist/categories)
(split by category) on the `dist` branch. Each entry's `repo_url` is what
you pass to `mip install github:<...>` — drop the `https://github.com/`
prefix and swap in `github:`.

**Before installing anything:** `mip install` fetches and runs third-party
code on your device. Nothing in this registry is code-reviewed — CI only
checks that a submission is well-formed and the repo exists, not that the
code itself is safe. See the [trust note in `SCHEMA.md`](SCHEMA.md#trust-note)
before installing from a package you don't already know.

**Short-name installs** (`mip install --index ... ina219-driver`, no full
repo path) are built and working (see [`worker/`](worker/)) but not yet
deployed to a public URL — not usable yet, direct `github:` install above
is the current way to install anything here.

## How it works (architecture)

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

- **[`index.json`](https://github.com/SolderedElectronics/micropython-registry/blob/dist/index.json)**
  / **`categories/*.json`** on the [`dist` branch](https://github.com/SolderedElectronics/micropython-registry/tree/dist)
  (not `main`) — generated from `packages.txt` by
  [`scripts/build_index.py`](scripts/build_index.py), rebuilt on every merge
  to `main` and on a daily schedule (so author-side edits that never touch
  this repo still get picked up eventually). Kept on its own orphan branch
  rather than `main` so purely-generated content doesn't bloat real history
  or fight `main`'s branch protection. This is what a future website
  (Phase 4) or any other tool reads — not `packages.txt` directly.

## Submitting a package

See [`CONTRIBUTING.md`](CONTRIBUTING.md) / [`SCHEMA.md`](SCHEMA.md#submitting-a-package)
for the full steps. Short version: add `mpy-registry.yaml` to your repo's
root, open a PR here adding your repo's URL to `packages.txt`.

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
- [x] Phase 3 — index generation (`dist/index.json`, `dist/categories/*.json`)
- [ ] Phase 4 — discovery website
- [ ] Phase 5 — launch / seed content
- [x] Phase 6 — custom mip index (optional, later) — [`worker/`](worker/), verified against real hardware; not yet deployed to a public URL (needs a Cloudflare account)

## License

MIT.

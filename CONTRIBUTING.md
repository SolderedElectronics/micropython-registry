# Contributing

## Submitting a package

See [`SCHEMA.md`](SCHEMA.md#submitting-a-package) for the full manifest spec
and steps. Short version:

1. Add an `mpy-registry.yaml` manifest to the root of **your own** package
   repo (copy [`examples/mpy-registry.yaml`](examples/mpy-registry.yaml) as
   a starting point). GitHub repos only for now.
2. Open a PR against **this** repo adding your repo's URL as one new line to
   [`packages.txt`](packages.txt), alphabetically sorted. Don't touch any
   other files in this PR.
3. CI validates your manifest and merges automatically on success — see
   [`SCHEMA.md`'s trust note](SCHEMA.md#trust-note) for what that does and
   doesn't mean.

If CI fails, the job log tells you exactly which check failed and why
(unreachable repo, missing manifest, schema mismatch, or name collision).
Fix your own repo/manifest and push again to the same PR branch — no need
to open a new one.

## Changing anything else in this repo

Schema/docs/CI changes are regular PRs, reviewed like any other project —
the auto-merge behavior above only applies to `packages.txt` changes.

<!--
Submitting a package? See CONTRIBUTING.md / SCHEMA.md for the full flow.
This PR should touch ONLY packages.txt.
-->

- [ ] I added `mpy-registry.yaml` to the root of my own package's repo
- [ ] This PR adds only one or more new lines to `packages.txt`, alphabetically sorted, and touches no other files
- [ ] My repo is public on GitHub (private repos can't be fetched by CI or by `mip install`)

CI will validate your manifest and merge this PR automatically on success -
no further action needed from you. If it fails, the job log will say why.

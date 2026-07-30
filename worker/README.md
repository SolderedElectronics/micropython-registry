# mip index worker (Phase 6)

A thin Cloudflare Worker implementing mip's actual index-query protocol, so
packages in this registry can be installed by short name instead of a full
`github:org/repo` path:

```
mpremote mip install --index https://<this-worker>.workers.dev ina219-driver
```

It is a translation layer only - it reads the same
[`dist/index.json`](https://github.com/SolderedElectronics/micropython-registry/blob/dist/index.json)
Phase 3 already generates and reshapes each package's entry into the JSON
shape mip expects at `/package/<mpy_version>/<name>/<version>.json`. See
[`src/index.js`](src/index.js) for the implementation notes, including a
real correctness bug found (and fixed) by reading mip's actual source rather
than assuming the protocol from docs: unpinned installs pass the literal
string `"latest"` as a git branch/tag name when resolving `github:` shorthand
URLs, which silently 404s unless resolved to a full `https://` URL first.

**Verified against real hardware**, not just simulated: ran the actual
unmodified `mip` module (MicroPython 1.28.0) on a real ESP32
(Soldered/Generic ESP32 module), over WiFi, against a local instance of this
Worker (`wrangler dev`) - `mip.install("ina219-driver", index=...)` completed
and the installed file was confirmed byte-identical to the source repo.

## Limitations (by design, for now)

- **GitHub repos only** - matches the rest of this registry; `gitlab:`/
  `codeberg:` shorthand in a package's own `package.json` is passed through
  unresolved rather than rejected, so it may still work if mip itself
  handles it, but isn't actively supported here.
- **No version pinning** - only `latest` (or whatever string matches the
  package's current version in the index) is served. The registry doesn't
  keep historical releases, so there's nothing to serve for older versions.
- **No `hashes`-based content addressing** - that's specific to
  micropython.org's own CDN storage model. Packages here stay hosted in
  their own repos, so only the `urls` field is used.

## Deploying

This requires a Cloudflare account - deploying isn't something that can be
done without one, so these are manual steps:

```sh
cd worker
npx wrangler login       # one-time browser auth
npx wrangler deploy
```

This publishes to `https://micropython-registry-index.<your-subdomain>.workers.dev`
by default. Add a custom domain (e.g. `packages.<project>.com`) via the
Cloudflare dashboard once you have one you want to use - matches the
project plan's original phrasing (`--index https://packages.<project>.com`).

### Local testing without deploying

```sh
cd worker
npx wrangler dev --ip 0.0.0.0   # --ip 0.0.0.0 needed for a real device on the same LAN to reach it
```

Then from a real board on the same network:

```sh
mpremote connect <port> mip install --index http://<this-machine's-LAN-IP>:8787 <package-name>
```

## Configuring a persistent default index

**Correction to the original project plan:** it assumed a
`mpremote mip config` step existed for setting a persistent default index.
Checked against `mpremote` 1.28.0 directly - **no such command exists**.
`mpremote mip --help` only exposes a per-invocation `--index` flag; there is
no `mpremote config` command at all.

As of today, there is no way to make `mip`/`mpremote` default to a custom
index persistently. The only real options:

1. **Pass `--index` every time** (simplest, works today):
   ```sh
   mpremote mip install --index https://<this-worker>.workers.dev ina219-driver
   ```
   or on-device:
   ```python
   import mip
   mip.install("ina219-driver", index="https://<this-worker>.workers.dev")
   ```
2. **Bake it into your own project's `boot.py`/setup script** if you want a
   project-local default - e.g. a helper function that always passes your
   index URL, so your own scripts don't repeat it. This is a workaround at
   the application level, not a real mip/mpremote feature.

If a persistent-default mechanism gets added to mpremote/mip upstream in the
future, this section needs revisiting - but as of `mpremote` 1.28.0, this
is the real, verified behavior.

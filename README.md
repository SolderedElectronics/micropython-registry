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

**Finding a package:** there's no browsable website yet, so for now browse
the package list directly:
[`index.json`](https://github.com/SolderedElectronics/micropython-registry/blob/dist/index.json)
(all packages) or
[`categories/`](https://github.com/SolderedElectronics/micropython-registry/tree/dist/categories)
(split by category). Each entry's `repo_url` is what you pass to
`mip install github:<...>` — drop the `https://github.com/` prefix and
swap in `github:`.

**Before installing anything:** `mip install` fetches and runs third-party
code on your device. Nothing in this registry is code-reviewed — CI only
checks that a submission is well-formed and the repo exists, not that the
code itself is safe. See the [trust note in `SCHEMA.md`](SCHEMA.md#trust-note)
before installing from a package you don't already know.

Installing by short package name alone (no repo path) isn't available yet —
use the direct `github:` install above for now.

## Submitting a package

Want to add your own package? See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT.

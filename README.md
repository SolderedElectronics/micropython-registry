# MicroPython Package Registry

A searchable index for MicroPython packages that live scattered across individual GitHub repos.

## Browsing and installing packages

> [!NOTE]
> This is still in development, we are working on easier integration with `mpremote`.

The easiest way to browse and install packages is the
[**MicroPython Helper**](https://marketplace.visualstudio.com/items?itemName=SolderedElectronics.soldered-micropython-helper)
extension for VS Code — search the registry by name or category and install
a package straight to a connected board with one click, no manual
`mip install` commands needed. This is the primary, recommended way to use
the registry.

Prefer the command line? Every package here stays hosted in its own GitHub
repo, so you can also install it the same way you'd install any
`mip`-compatible package directly from GitHub:

```sh
mpremote mip install github:SolderedElectronics/Soldered-MicroPython-INA219
```

or from the device's own REPL:

```python
import mip
mip.install("github:SolderedElectronics/Soldered-MicroPython-INA219")
```

**Before installing anything:** `mip install` fetches and runs third-party
code on your device. Nothing in this registry is code-reviewed. There are CI only
checks that a submission is well-formed and the repo exists, not that the
code itself is safe. See the [trust note in `SCHEMA.md`](SCHEMA.md#trust-note)
before installing from a package you don't already know.

## Submitting a package

Want to add your own package? See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT.

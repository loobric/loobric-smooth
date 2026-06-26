# loobric-smooth

Python client for [Smooth Core](https://github.com/loobric/smooth-core) — the
library and CLI for synchronizing CNC tool data. It speaks only the public REST
API and depends on nothing from the server.

> **New in v0.4.0 — a seed script + a public sandbox.**
> [`examples/quickstart.sh`](examples/quickstart.sh) is a readable list of plain
> `smooth` commands that seeds an account with a small demo catalog (two
> manufacturers) and walks the whole loop — machine → catalog → instance → tool
> set → tool-table push. Run it to give a fresh account something to explore;
> read it to learn how to script the CLI. Point it at the free hosted sandbox and
> kick the tires without installing a server. See [docs/SANDBOX.md](docs/SANDBOX.md).
>
> **New in v0.3.0 — full list/show symmetry.** Every listable entity now has a
> matching `show` verb: `show-machine`, `show-tool`, and `show-key` join the
> existing `show-*` commands, each resolving its target by id, name, or unique
> prefix. List to find it, show to inspect it — one consistent pattern everywhere.
>
> **`smooth import` — stop re-typing tool data.** One command auto-detects the
> format and turns a vendor export into catalog records on your server:
> **DIN 4000** (CSV + XML 2013/2016), **STEP P21**, **GTC packages** (ISO 13399),
> **SolidCAM**, and **hyperMILL**. Every imported field keeps its source, and the
> raw payload is preserved verbatim so nothing is lost or guessed. GTC packages
> also carry the tool's 3D STEP models and images, uploaded as canonical media on
> servers whose media backend is enabled. See
> [docs/IMPORTERS_PLAN.md](docs/IMPORTERS_PLAN.md).
>
> The importable library (`smooth_client.Client`) and the `smooth` CLI are both
> here, ported from the old single-file `loobric.py` — see
> [docs/adr/0001-extract-loobric-smooth.md](docs/adr/0001-extract-loobric-smooth.md).

## Install

```bash
pip install loobric-smooth   # library + CLI + every bundled importer — stdlib only, no deps
```

Everything ships in the base install. The library, the `smooth` CLI, and all of
today's importers (DIN 4000, STEP P21, GTC, SolidCAM, hyperMILL) are
standard-library only, so the package stays vendorable and runs in constrained
interpreters. The optional `[importers]` extra is reserved for future formats
that need heavier parsers; no bundled importer requires it yet.

## Try the sandbox

Don't want to run a server yet? Point the client at the free hosted **sandbox**
and explore against live data:

```bash
pip install loobric-smooth
export SMOOTH_BASE_URL=https://api.loobric.com
smooth register you@example.com        # create an account
smooth login you@example.com           # then mint a key (below)
smooth create-key sandbox --scopes "read write"
export SMOOTH_API_KEY=<the key it prints>    # the CLI reads this automatically
curl -O https://raw.githubusercontent.com/loobric/loobric-smooth/master/examples/quickstart.sh
bash quickstart.sh                     # seed a demo and walk the loop
```

The sandbox is a shared demo server — **data may be reset and accounts removed,
so keep nothing real there.** Full walkthrough (and why API keys, not sessions):
[docs/SANDBOX.md](docs/SANDBOX.md).

## Library

```python
from smooth_client import Client, NotFound

c = Client(base_url="http://nas:8000", api_key="...")   # solo mode: omit api_key
for s in c.list_tool_sets():
    print(s)
```

Every method returns parsed data and raises a `SmoothClientError` subclass
(`NotFound`, `AuthRequired`, `HTTPError`, `ConnectionFailed`) on failure — it
never prints or exits, so callers handle failure themselves.

## CLI

`smooth <verb>` is the universal command-line client (the role the old `loobric`
command served). See the [CLI reference and walkthrough](docs/CLI.md).

```bash
smooth --help
smooth list-machines
smooth show-machine mill01            # by name, id, or unique prefix
smooth create-record --from-catalog B201 --name "1/4 downcut"
smooth show-tool "1/4 downcut"        # one instance, full provenance
```

Every `list-*` verb has a matching `show-*` verb (`show-machine`, `show-tool`,
`show-tool-set`, `show-key`, …), each resolving its target by id, name, or
unique prefix — list to find it, show to inspect it.

### Importing tool data

`smooth import` reads a vendor export, detects the format, and creates catalog
records on the server. Use `--dry-run` to see exactly what would be created
without sending anything:

```bash
smooth import tools.csv --dry-run        # DIN 4000 CSV — preview only
smooth import tools.xml                   # DIN 4000 / SolidCAM / hyperMILL (by XML root)
smooth import catalog.p21                  # STEP P21
smooth import package.zip                  # GTC package (ISO 13399) + 3D models & images
```

Re-importing the same catalog is detected by natural key and reported as
*skipped*, never duplicated.

## License

MIT. (The server, Smooth Core, is AGPL-3.0; this client is MIT so it can be
freely vendored and reused.)

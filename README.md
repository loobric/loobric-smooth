# loobric-smooth

Python client for [Smooth Core](https://github.com/loobric/smooth-core) — the
library and CLI for synchronizing CNC tool data. It speaks only the public REST
API and depends on nothing from the server.

> **Status:** the importable library (`smooth_client.Client`) and the `smooth`
> CLI are here, ported from the old single-file `loobric.py`. `smooth import`
> reads **DIN 4000** (CSV/XML), **STEP P21**, **GTC packages** (ISO 13399, with
> 3D models + images uploaded as canonical media), **SolidCAM**, and **hyperMILL**
> exports — see [docs/IMPORTERS_PLAN.md](docs/IMPORTERS_PLAN.md). See
> [docs/adr/0001-extract-loobric-smooth.md](docs/adr/0001-extract-loobric-smooth.md).

## Install

```bash
pip install loobric-smooth            # library + CLI + DIN 4000 import (stdlib only, no deps)
pip install "loobric-smooth[importers]"   # + heavier-dependency importers (GTC/P21/..., when added)
```

DIN 4000 import is stdlib-only and works with the base install; the `[importers]`
extra is for formats that need extra parsers (e.g. STEP/P21).

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
smooth create-record --from-catalog B201 --name "1/4 downcut"
```

## License

MIT. (The server, Smooth Core, is AGPL-3.0; this client is MIT so it can be
freely vendored and reused.)

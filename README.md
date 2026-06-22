# smooth-client

Python client for [Smooth Core](https://github.com/loobric/smooth-core) — the
library and CLI for synchronizing CNC tool data. It speaks only the public REST
API and depends on nothing from the server.

> **Status:** extraction in progress. The importable library (`smooth_client.Client`)
> is here; the CLI and format importers are being ported from the old single-file
> `loobric.py`. See [docs/adr/0001-extract-smooth-client.md](docs/adr/0001-extract-smooth-client.md).

## Install

```bash
pip install smooth-client            # library + CLI (stdlib only, no deps)
pip install "smooth-client[importers]"   # + format importers (DIN4000/GTC/P21/...)
```

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

`smooth <verb>` — *coming with the CLI port.* It will be the universal
command-line client (the role the old `loobric` command served).

## License

MIT. (The server, Smooth Core, is AGPL-3.0; this client is MIT so it can be
freely vendored and reused.)

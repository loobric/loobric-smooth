# Changelog

All notable changes to **loobric-smooth** (the Smooth client library + `smooth` CLI)
are recorded here. This project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0] — 2026-06-26

### Added
- **`examples/quickstart.sh`** — a readable shell script of plain `smooth`
  commands that seeds an account with a small demo (a handful of endmills,
  drills, a V-bit, a face mill, across two plausible manufacturers) and walks
  the whole loop: machine → catalog → instance → tool set → tool-table push.
  Run it to populate a fresh or sandbox account; read it to learn how to script
  the CLI. (No new `smooth` subcommand — it's just the commands you'd type.)
- **`docs/SANDBOX.md`** — an API-key-first walkthrough for the free hosted
  sandbox at `https://api.loobric.com`.

### Changed
- **`SMOOTH_API_KEY` is now read from the environment automatically.** Export it
  once (as `create-key` already advises) and every command authenticates with
  the key — no need to repeat `--api-key`. Precedence is `--api-key` flag >
  `SMOOTH_API_KEY` env > saved session cookie. This is the right default for the
  sandbox, where login sessions are dropped on each server redeploy but API keys
  persist.
- **`smooth register` now pins the server it ran against** (saves `base_url` to
  `~/.smooth/session.json`), so the next command targets the same server without
  re-passing `--base-url`.
- The "Base URL required" error now names the one-liner to fix it
  (`export SMOOTH_BASE_URL=…`).

## [0.3.0] — 2026-06-23

### Added
- **`show-machine`, `show-tool`, `show-key`** — every listable entity now has a
  matching show verb (full list/show symmetry). Each resolves by id, name, or
  unique prefix. `show-tool` prints a tool instance with full provenance;
  `show-machine` adds its tool-table summary and linked sets; `show-key` resolves
  one API key.

## [0.2.0] — 2026-06-22

### Added
- **`smooth import` — tool-data importers.** One command auto-detects the format
  and turns a vendor export into catalog records on the server. Supported:
  - **DIN 4000** — CSV and XML (ToolsUnited 2013 & 2016 editions, incl. the
    decimal-comma variant).
  - **STEP P21** (ISO 13399) — identity and geometry read from the inline ISO
    13399 mnemonics; no property dictionary required.
  - **GTC packages** (`.zip`, ISO 13399) — both GTC 2.x and the GTC 2017 /
    ToolsUnited inner-zip layout. The tool's 3D STEP models and images are
    uploaded as canonical media on servers whose media backend is enabled.
  - **SolidCAM** (`<Results>` XML) and **hyperMILL** (OPEN MIND `omtdx` XML).
  - `--dry-run` previews exactly what would be created without sending anything;
    `--no-preserve` skips storing the raw source payload.
- **`Client.upload_media()`** — attach a file (3D model, drawing, image) to a
  record's canonical media (stdlib multipart).
- Importers are an opt-in subpackage (`smooth_client.importers`) with a public
  `parse()` entry point returning `CatalogRecordDraft`s.

### Design
- Every importer is **standard-library only** — the package stays vendorable and
  runs in constrained interpreters. The `[importers]` extra is reserved for
  future formats that need heavier parsers; no bundled importer requires it.
- Imports never fabricate: a field the source does not state stays `unknown`
  (`shape` comes only from a source-declared class/type, never inferred), the
  server stamps `asserted:<source>` provenance, the raw payload is preserved
  verbatim, and a re-imported catalog is skipped via its natural key, not
  duplicated.

## [0.1.0]

### Added
- Initial extraction of the Smooth client from the single-file `loobric.py`: the
  importable `smooth_client.Client` library and the `smooth` CLI, plus PyPI
  packaging (Trusted Publishing) and CI.

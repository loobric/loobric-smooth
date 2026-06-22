# Format Importers — Plan

Tracks [smooth-core#31](https://github.com/loobric/smooth-core/issues/31).
This is the plan for importing tool data from known external formats into Smooth.
It lives in `loobric-smooth` because importing is a **client** job: an importer
parses a file and pushes the result through the public API. The server never
parses a vendor format.

> Status: planning. Nothing here is built yet. The `[importers]` extra in
> `pyproject.toml` reserves the dependency slot; this document says what fills it.

---

## 1. The ten formats are really three

The issue lists ten format names. External research (five parallel briefs,
2026‑06‑22, sources at the end) shows they **collapse to three lineages**, and
several of the named "formats" are not parseable targets at all — they are
proprietary systems whose only realistic interop path is to export *one of the
three open formats*.

| Issue line item | Reality |
|---|---|
| DIN4000 (CSV) | **DIN 4000** lineage — flat semicolon CSV of a tool class's property table |
| DIN4000 (XML2013) | **DIN 4000** lineage — DIN 4000‑102 XML, one schema edition |
| DIN4000 (XML2016) | **DIN 4000** lineage — DIN 4000‑102 XML, a later edition |
| GTC (GTC17) | **ISO 13399 / GTC** lineage — a GTC package version (≈ GTC v2.1.0, 2017) |
| GTC (GTC20) | **ISO 13399 / GTC** lineage — *no public 2020 release found*; verify |
| P21 (P21) | **ISO 13399 / GTC** lineage — P21 **is** how ISO 13399 serializes; the `.p21` files *inside* a GTC package |
| TDM (TDM) | proprietary system → **exports ISO 13399 / GTC**; no parseable native format |
| Zoller (Zoller) | proprietary system → **exports ISO 13399 / DIN 4000**; `zidCode` is an undocumented 2D‑barcode payload, not a file |
| SolidCAM (SolidCAM) | **SolidCAM** lineage — does *not* speak open standards; path is its CSV/XLS export |
| HyperMill (HyperMill) | proprietary DB → **exports ISO 13399 / GTC / STEP**; native `.db`/`.mdb` schema undocumented |

**So the actual engineering targets are:**

1. **DIN 4000** — a CSV reader and an XML reader (two schema editions).
2. **ISO 13399 / GTC / P21** — a GTC‑package reader (ZIP + `package_assortment.xml`) and a P21 property reader. This one target *also* satisfies GTC17, GTC20, TDM, Zoller, and HyperMill, because all of those export it.
3. **SolidCAM** — a CSV/XLS reader for SolidCAM's own export.

The proprietary natives (TDM database, Zoller `zidCode`/z.One, HyperMill `.db`/`.mdb`,
SolidCAM `.TAB`/`.tlv`/`.tls`/`.tlm`) are **out of scope** and should stay out:
they are undocumented, vendor‑gated, and reverse‑engineering‑bound with no public
samples. The documented, supported way to get data out of all of them is the open
export. We import the open export; we do not chase the binaries.

---

## 2. Samples: solved — the source is Kennametal

The ten label strings are **Kennametal's export/download format menu.** The
maintainer can export real tool data from Kennametal in any of them, which means
**every format has a reachable sample and we test against real files, not
guesses.** (Kennametal is a GTC founding member, which is why its export menu
spans the whole DIN 4000 / GTC / P21 / TDM / Zoller / SolidCAM / HyperMill set —
it re‑emits its catalog in each downstream format.) This retires the dominant
risk every research brief flagged below.

Phase 0 is therefore trivial: **export the target format from Kennametal, commit
a trimmed sample as a test fixture, and build the mapping against its real
columns/elements.** We still write no mapping for a format until its Kennametal
export is in hand.

Original research caveat, retained for context: **the exact label strings do not
resolve to a public specification** —

- "DIN4000 (XML2013)" / "(XML2016)" — DIN 4000‑102 is real and is the XML
  exchange schema, but it is **paywalled (~€105)** and the XSD ships inside the
  purchased standard. The "2013"/"2016" editions can't be diffed without the
  redline or two sample files.
- "GTC17"/"GTC20" — GTC versions semantically (latest verified **2.1.1, May 2018**);
  no public 2020 release was found. The year labels are not official.
- The parenthetical‑repeat style (`TDM (TDM)`, `Zoller (Zoller)`) strongly
  suggests these strings were **copied verbatim from another application's
  import‑source dropdown** (a portal like ToolsUnited/MachiningCloud, or a CAM
  importer). Knowing which one would hand us the field mappings directly.

**Field names, CSV headers, XML element names, and the P21 property‑code → meaning
mapping cannot be locked without a real file of each format.** Guessing them is
exactly the "every imported tool became an endmill" failure the schema exists to
prevent. Therefore Phase 0 is *acquire one real sample per format*, and we do not
write a mapping for a format we have not seen.

Sample sources that exist (most need a free account):
- **MachiningCloud** — 40+ vendors (Sandvik, Kennametal, Walter, …), GTC packages.
- **ToolsUnited / CIMSOURCE** — DIN 4000 *and* ISO 13399/GTC exports.
- **Sandvik CoroPlus Tool Library**, **ISCAR e‑catalog** (`.p21`), **Mitsubishi** — vendor catalogs.
- **GTC demo package** on gtc-tools.com (GTC 2.0 sample).
- **SolidCAM** — generate a CSV/XLS export from the app itself (Harvey/Helical ship `.TAB` libraries, but `.TAB` is the binary we're avoiding).

---

## 3. Architecture

The importer is a **pure parse‑and‑map function**. It never opens a socket.

```
source file  ──parse──▶  ToolDescriptor(s)  ──map──▶  canonical fields  ──▶  Client.create_catalog_record(...)
  (bytes)               (importer-internal,            ({name, manufacturer,      (existing API; server
                         normalized intermediate)        product_code, geometry,    stamps asserted:<source>)
                                                          item_type})
```

- **`smooth_client/importers/`** — a subpackage, imported only when the
  `[importers]` extra is installed. The stdlib‑only promise of the core
  (`Client`, `transport`, `cli`) is unaffected; heavy deps live here and nowhere
  else. CI already runs the base on 3.9/3.12 with no deps to guard this.
- **Each importer exposes `parse(path_or_bytes) -> list[CatalogRecordDraft]`.**
  A `CatalogRecordDraft` is a plain dataclass: the canonical `fields` dict
  (`name`, `manufacturer`, `product_code`, nominal `geometry.*`, optional
  `item_type`) **plus** the raw source document to preserve. No HTTP, no
  provenance strings — the importer states *values*, not *sources*.
- **A thin driver** (`importers/run.py` + a `smooth import` CLI verb) takes the
  drafts and calls the existing `Client.create_catalog_record(source=..., fields=...)`.
  The **server** stamps `asserted:<source>` on every field (the client never
  writes provenance — TOOL_SCHEMA §3.2/§4). The raw source document is written
  into the client section via `sync_client_section(..., client="import:<fmt>",
  data={"source_document": ...})` so the import is lossless and re‑runnable.

### Provenance & the endmill rule (non‑negotiable)

- Importers create **`ToolCatalogRecord`s** (catalog *types*), never instances,
  never tool‑table entries. A catalog import is exactly the `catalog-import`
  scope in TOOL_SCHEMA §10: "asserts nominal geometry; never touches instances
  or entries."
- All geometry is **nominal**, stamped `asserted:<format>-import` by the server.
  Nothing is `observed` — an importer measured nothing.
- **A field the source does not state stays `unknown`.** Most critically:
  `geometry.shape`/`item_type` is asserted **only** when the source explicitly
  carries it (an ISO 13399 class code, a DIN class). We never infer "endmill"
  from a diameter. Missing is `unknown`, not a guess.
- `product_code` + `manufacturer` are the natural key; re‑importing the same
  catalog must hit the server's natural‑key `409` path (M2 behaviour), not mint
  duplicates.

### Dependencies (kept minimal, all behind `[importers]`)

| Lineage | Parser | Dep |
|---|---|---|
| DIN 4000 CSV | stdlib `csv` | none |
| DIN 4000 XML | stdlib `xml.etree.ElementTree`; `lxml` only if XSD validation needed | `lxml` (optional) |
| GTC package | stdlib `zipfile` + `xml.etree` for `package_assortment.xml` | none |
| P21 properties | `steputils` (MIT, pure‑Python P21 DOM) — or a ~300‑line hand‑rolled tokenizer for zero deps | `steputils` |
| SolidCAM CSV | stdlib `csv` | none |
| SolidCAM XLSX | `openpyxl` (legacy `.xls` → `xlrd`) | `openpyxl` (optional) |

Note: the current `[importers] = ["lxml>=5.0"]` slot should be split into
narrower extras (e.g. `[din4000]`, `[gtc]`, `[solidcam]`) or kept as one
umbrella — decide when the first parser lands. **OCC / pythonocc is explicitly
rejected**: a 3D CAD kernel is hundreds of MB and we never parse BREP geometry
(the 3D `.stp` models inside a GTC package are ignored).

---

## 3a. DIN 4000 — verified from the real Kennametal files

Three corrections/confirmations the actual exports forced on the research:

- **DIN 4000 uses its own class‑specific feature codes, NOT ISO 13399 mnemonics.**
  The columns are `A1`, `B2`, `C3`, `J22`… (DIN *Sachmerkmal* codes), keyed by
  the `NSM` class (`DIN4000-82` = solid endmills) — *not* `DC`/`LF`/`ZEFF` (those
  are the GTC/P21 lineage). So the code→field map is **per DIN class**; this
  file is the `DIN4000-82` map, and a drill class would need its own.
- **Decimal format varies by export variant, not by format.** CSV and XML‑2013
  use a decimal *point* (`1.588`); XML‑2016 uses a decimal *comma* (`1,588`). The
  mapper parses numbers comma‑tolerantly per‑field — and must *not* blanket‑
  replace commas, because `J8` is a comma‑*list* (`"FZI,FSE,…"`).
- **No legend in the export.** Neither the CSV, the XML, nor the ToolsUnited DTD
  carries human‑readable names for the codes. Meaning for the unmapped codes
  (`B2`, `B3`, `C4`, the `D`/`F`/`H` series) needs the paywalled DIN 4000‑82
  text. They are preserved verbatim, never guessed.

**Shipped `DIN4000-82` mapping** (`din4000/_codes.py`), cross‑validated against
the description `ENDMILL … 1/16X1/8X1/8X1 1/2` and order code:

| DIN code | → canonical | value |
|---|---|---|
| `J23` | `name` | ENDMILL H1TE 1/16X1/8X1/8X1 1/2 S |
| `J3` | `manufacturer` | KH (Kennametal supplier code — passed through, not expanded) |
| `J22` | `product_code` | H1TE4SE0063R013HA_KCPM15 |
| `A1` | `geometry.diameter` | 1.588 mm |
| `C3` | `geometry.shank_diameter` | 3.175 mm |
| `B5` | `geometry.length` | 38.1 mm |
| `F21` | `geometry.flutes` | 4 |
| `NSM`=`DIN4000-82` | `geometry.shape` | endmill *(the class **declares** the type — read, not inferred)* |

All map to keys the server's `Geometry` contract model actually defines (verified
against `smooth/contract/models.py`), so none get rejected or silently dropped.

## 4. The hard part: ISO 13399 property semantics

> **Update (resolved by the real files):** the research feared we'd need the
> paywalled PLIB dictionary to decode P21 property codes. We don't — the
> CIMSOURCE/ToolsUnited generator writes the readable ISO 13399 mnemonic into
> every value entity (`NUMERICAL_VALUE('DC', …)`, `STRING_VALUE('GRADE', …)`),
> exactly like DIN's codes. A curated mnemonic map (DC/OAL/APMX/ZEFF/DCONMS…)
> covers the geometry; the opaque `PLIB_*_REFERENCE` codes are ignored. The text
> below is kept for the general case (a P21 lacking inline mnemonics would still
> need the dictionary).

P21/STEP is **easy to tokenize, hard to interpret.** A `.p21` file stores values
against opaque PLIB property codes (e.g. `PLIB_PROPERTY_REFERENCE('71CF29872F0AB', …)`),
not human labels. Turning a code into "cutting diameter" requires the **ISO 13399
reference dictionary (ISO/TS 13399‑3xx, PLIB / ISO 13584‑25)** — copyrighted and
fee‑based. We **cannot redistribute** it.

Two mitigations, both verified:

1. **Prefer the GTC package XML over the P21 for identity.** `package_assortment.xml`
   carries human‑readable product id, order code, manufacturer, classification,
   and unit system in plain XML — no PLIB decode needed. For many tools this is
   enough for a useful catalog record (name + manufacturer + code + class), with
   geometry filled in opportunistically.
2. **Hand‑build a small code→field map from public manufacturer references.**
   Sandvik, Dormer Pramet, and Mitsubishi publish the common ISO 13399 codes
   openly. Verified codes we can map without the paid dictionary:

   | Code | Meaning | Maps to |
   |---|---|---|
   | `DC` | cutting diameter | `geometry.diameter` |
   | `DCON` / `DMM` | connection / shank diameter | `geometry.shank_diameter` |
   | `OAL` | overall length | `geometry.overall_length` |
   | `LF` | functional length | `geometry.functional_length` |
   | `LU` / `LCF` | usable / cutting length | `geometry.flute_length` |
   | `ZEFF` | effective cutting edges | `geometry.flutes` |
   | `NOF` | number of flutes | `geometry.flutes` |
   | `RE` | corner radius | `geometry.corner_radius` |

   This curated subset (≈ a dozen codes) covers the geometry the canonical schema
   actually models. Full PLIB decode stays an **optional, IP‑gated** capability,
   not a baseline feature. (`ZEFF` vs a distinct flute‑count code is a known
   ambiguity — resolve against a real file.)

---

## 5. Phasing (by ROI, given the research)

Ordered so the cheapest, highest‑coverage work lands first and the IP‑gated deep
decode comes last.

- **Phase 0 — Samples. ✅ DONE.** Kennametal exports of article `6767731` (a
  1/16″ 4‑flute endmill) obtained in CSV, XML 2013, and XML 2016, committed
  trimmed under `tests/fixtures/importers/`.
- **Phase 1 — Importer framework + DIN 4000 (CSV **and** XML). ✅ DONE.**
  `smooth_client/importers/` (`base.CatalogRecordDraft`, `run.import_drafts`
  driver, `din4000/` reader), the `smooth import <file>` CLI verb (`--dry-run`,
  `--no-preserve`, `--source`), fixtures and 12 tests (84 total green). Because
  CSV and both XML editions carry the *identical* DIN feature codes, one shared
  mapper (`din4000/_codes.py`) serves all three — so the XML work folded in here
  rather than a later phase. **The headline test invariant: all three variants
  parse to byte‑identical canonical fields.** Driver handles natural‑key `409`
  as *skipped*, preserves the full raw payload in the record's client section.
- **Phase 2 — GTC package + Phase 3 — P21 geometry. ✅ DONE (together).**
  `smooth_client/importers/p21.py` is a stdlib line tokenizer for STEP Part 21;
  `gtc.py` reads a GTC ZIP. **Key finding from the real Kennametal exports:** the
  CIMSOURCE/ToolsUnited P21 writes the human-readable ISO 13399 *mnemonic* into
  every value entity (`NUMERICAL_VALUE('DC', $, #119, '6.35')`), so identity AND
  geometry come straight out — **no `steputils`, no PLIB dictionary, stdlib
  only.** One reader handles **both** GTC 2.x and GTC 2017 (the ToolsUnited
  per-file inner-zip layout — unwrapped transparently). The 3D STEP models +
  images are extracted and uploaded as **canonical media** (smooth-core's new
  `media` feature). `shape` comes from the GTC class (`MILSQS → endmill`),
  `item_type` from the P21 `SPECIFIC_ITEM_CLASSIFICATION('tool item')`. Verified
  against real GTC17, GTC20, and standalone P21; 8 tests, synthetic fixtures.
- ~~**Phase 4 — DIN 4000 XML (2013 + 2016).**~~ **Folded into Phase 1.** One
  tolerant `etree` reader handles both ToolsUnited DTDs (`DIN_4000_Schema.dtd`
  and `..._2015.dtd`); they differ only in the `Main-Data` block and decimal
  format (point vs comma), both handled. New DIN 4000 *classes* (drills, etc.)
  still need their own per‑class code map (`_codes.CLASS_MAPS`) + a sample.
- **Phase 5 — SolidCAM CSV/XLS.** Separate lineage; drive off SolidCAM's own
  export (parametric milling tools only — 3D‑model‑defined tools don't export to CSV).

**Deferred / out of scope (document, don't build):** TDM native DB, Zoller
`zidCode`/z.One native, HyperMill `.db`/`.mdb`, SolidCAM `.TAB`/`.tlv`/`.tls`/`.tlm`.
For each, the README/docs should say "export ISO 13399 / GTC (or CSV) from the
vendor tool and import that."

---

## 6. Testing

- **Golden‑file fixtures**, mirroring smooth‑core's `tests/fixtures/schema/`
  approach: a tiny, synthetic (or minimally‑redacted) sample per format committed
  to `tests/fixtures/importers/`, plus the expected `CatalogRecordDraft` output.
  Parser tests run offline, no server.
- **No vendor data redistributed.** Fixtures are hand‑authored or trimmed to the
  few fields under test; we do not commit whole vendor catalogs (licensing, §7).
- **Round‑trip / lossless test:** the preserved `source_document` re‑parses to the
  same drafts.
- **The endmill guard:** an explicit test that a source *without* a type/shape
  produces a record whose `item_type`/`shape` is `unknown`, never inferred.

---

## 7. Licensing / IP

- **Writing parsers is fine.** Reading a file the user owns is legitimate; file
  formats are not copyrightable for interoperability.
- **Do not redistribute** the DIN 4000‑102 / ISO 13399 standard text or their
  XSDs, and **do not bundle the full PLIB reference dictionary** (paywalled). A
  hand‑built code map compiled from publicly‑published manufacturer subsets (§4)
  is fine; a complete dictionary is not — get a second look before bundling any
  large property table.
- **Parser library licenses:** `steputils` MIT (clean); `lxml` BSD; `openpyxl`
  MIT. The `mtconnect/iso_133399` repo is **not** OSI‑licensed (RAND patent
  terms) — do not vendor it.
- Vendor sample/catalog data is licensed for use, not redistribution — keep test
  fixtures synthetic/minimal.

---

## 8. Open questions for the maintainer

1. ~~Where did the format strings come from?~~ **Resolved: Kennametal's export
   menu** (§2). Field mappings come from real Kennametal exports.
2. **Split `[importers]` into per‑format extras**, or keep one umbrella?
3. **Do you want a `smooth import <format> <file>` CLI verb, a `Client` method,
   or both?** (Plan assumes both: a `parse()` library entry point + a CLI verb.)

### Decided
- **First target: DIN 4000 CSV** (cheapest end‑to‑end proof of the framework).

---

## Sources

DIN 4000 / ISO 13399 / GTC structure and codes:
- https://www.dinmedia.de/en/standard/din-4000-102/334644248 (DIN 4000‑102 XML exchange, editions, price)
- https://en.wikipedia.org/wiki/ISO_13399 ; https://www.iso.org/standard/36757.html (ISO 13399‑1)
- https://www.sandvik.coromant.com/en-gb/knowledge/machining-formulas-definitions/cutting-tool-parameters (property codes DC/LF/OAL/NOF/ZEFF/DMM/RE)
- https://www.mmc-carbide.com/us/technical_information/iso/iso13399_property
- https://gtc-tools.com/ ; GTC Package Specification 2.1.1: https://gtc-tools.com/wp-content/uploads/2016/12/GTC-Package-Specification-2.1.1.pdf
- GTC Technical White Paper (P21/PLIB/package layout): https://gtc-tools.com/wp-content/uploads/2016/12/Technical-White-Paper-31032015.pdf
- https://blogs.sw.siemens.com/news/digital-cutting-tool-catalogs-iso-13399-and-gtc/
- StOB / DIN↔ISO mapping: https://info.toolsunited.com/a-glimpse-into-the-background-history-of-standard-openbase-cimsource-awesome/

P21 / STEP Part 21:
- https://en.wikipedia.org/wiki/ISO_10303-21 ; http://www.steptools.com/stds/step/IS_final_p21e3.html
- steputils (MIT, pure‑Python): https://github.com/mozman/steputils ; https://steputils.readthedocs.io/en/latest/p21.html
- IfcOpenShell/step-file-parser: https://github.com/IfcOpenShell/step-file-parser
- STEPcode: https://stepcode.github.io/docs/home/
- mtconnect/iso_133399 (XSD/codegen; non‑OSI license): https://github.com/mtconnect/iso_133399

TDM / Zoller / SolidCAM / hyperMILL:
- https://www.tdmsystems.com/en/solutions/interfaces/ (DIN 4000 / ISO 13399 / GTC compatible)
- https://www.zoller.info/us/products/tool-management/data-transfer/zidcode.html
- https://www.solidcam.help/2021/milling/NTT_Importing_from_TAB_tool_libraries.htm ; https://www.solidcam.help/2021/milling/NTT_Exporting_Tool_Items_Components.htm
- https://www.openmind-tech.com/en-us/cam/automated-programming/tool-database/
- https://info.toolsunited.com/solidcam/ ; https://go2cam.scrollhelp.site/en/go2cam/help/standardization-of-tools

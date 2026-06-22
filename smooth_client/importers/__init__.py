# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT
"""Format importers: parse a vendor tool-data export into catalog records.

An importer is a *pure parse-and-map* step. It never opens a socket: it turns a
file into one or more :class:`CatalogRecordDraft` (canonical `fields` + the raw
source payload to preserve). The :mod:`smooth_client.importers.run` driver is
what pushes those drafts through the public API — so parsing is offline,
testable, and the network concern lives in exactly one place.

Importers create **ToolCatalogRecords only** (catalog *types*), with nominal
geometry the server stamps `asserted:<source>`. They never observe, never touch
instances or entries, and — critically — never *infer* a field the source did
not state. A code we cannot pin to a meaning is preserved verbatim, never
guessed (the "every imported tool became an endmill" failure the schema exists
to prevent).
"""
from pathlib import Path
from typing import List, Union

from smooth_client.importers.base import CatalogRecordDraft, MediaFile

__all__ = ["CatalogRecordDraft", "MediaFile", "parse"]


def parse(path: Union[str, Path]) -> List[CatalogRecordDraft]:
    """Detect the format from the file and dispatch to the right importer.

    - ``.zip`` (or a PK header) → GTC package (ISO 13399, with media)
    - ``.p21`` / ``.stp`` / ``.step`` / an ``ISO-10303-21`` header → STEP P21
    - everything else → DIN 4000 (CSV or XML)
    """
    name = str(path).lower()
    head = Path(path).read_bytes()[:32]
    if name.endswith(".zip") or head[:2] == b"PK":
        from smooth_client.importers import gtc
        return gtc.parse(path)
    if (name.endswith((".p21", ".stp", ".step"))
            or head.lstrip().startswith(b"ISO-10303-21")):
        from smooth_client.importers import p21
        return p21.parse(path)
    from smooth_client.importers import din4000
    return din4000.parse(path)

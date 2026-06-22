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
from smooth_client.importers.base import CatalogRecordDraft

__all__ = ["CatalogRecordDraft"]

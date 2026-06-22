# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT
"""The importer-internal intermediate: a parsed, not-yet-created catalog record."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# The identity floor every catalog record needs (the natural key is
# manufacturer + product_code; name is required by the contract).
IDENTITY_FIELDS = ("name", "manufacturer", "product_code")


@dataclass
class CatalogRecordDraft:
    """One catalog record a parser produced, before it is sent.

    Pure data — no provenance, no network. ``fields`` is the canonical
    ``{value, unit?}`` leaf map :meth:`Client.create_catalog_record` expects
    (the server stamps the ``asserted:<source>`` provenance). ``raw`` is the
    full source payload, kept verbatim so the import is lossless and the
    unmapped source codes survive for later promotion.
    """

    fields: Dict[str, Any]
    raw: Dict[str, Any]
    source_format: str                       # e.g. "din4000-csv" / "din4000-xml"
    source_class: Optional[str] = None        # e.g. "DIN4000-82"

    def _leaf_value(self, key: str) -> Any:
        leaf = self.fields.get(key)
        return leaf.get("value") if isinstance(leaf, dict) else None

    @property
    def name(self) -> Any:
        return self._leaf_value("name")

    @property
    def manufacturer(self) -> Any:
        return self._leaf_value("manufacturer")

    @property
    def product_code(self) -> Any:
        return self._leaf_value("product_code")

    def missing_identity(self) -> List[str]:
        """The identity fields with no value — a draft missing any of these
        should be skipped, not sent as a malformed record."""
        return [k for k in IDENTITY_FIELDS if not self._leaf_value(k)]

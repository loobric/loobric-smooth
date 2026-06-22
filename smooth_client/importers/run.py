# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT
"""Drive an importer's drafts into a Smooth server through the public API.

Each draft becomes a ``ToolCatalogRecord`` via ``create_catalog_record`` — the
server stamps ``asserted:<source>`` on every canonical field; the client never
writes provenance. The full source payload is then preserved verbatim in the
record's own client section (the sync door), so the import is lossless and the
unmapped source codes survive for later promotion. Re-importing the same catalog
hits the server's natural-key ``409`` and is reported as *skipped*, never
duplicated.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from smooth_client.errors import HTTPError, SmoothClientError


@dataclass
class ImportReport:
    """The outcome of an import run, partitioned so a caller (CLI or tests) can
    report precisely what happened to each draft."""

    created: List[Tuple[Any, dict]] = field(default_factory=list)
    skipped: List[Tuple[Any, str]] = field(default_factory=list)
    failed: List[Tuple[Any, Exception]] = field(default_factory=list)
    # Created, but storing the raw payload afterward failed — the canonical
    # record exists; only the lossless copy is missing. Surfaced, not swallowed.
    preserve_failed: List[Tuple[Any, Exception]] = field(default_factory=list)


def import_drafts(client, drafts, *, source: str = "din4000-import",
                  client_name: str = "import:din4000", preserve: bool = True,
                  on_event: Optional[Callable[[str, Any, Any], None]] = None) -> ImportReport:
    """Create a catalog record per draft. ``on_event(kind, draft, info)`` is
    called for progress (kinds: ``create``/``skip``/``fail``/``preserve_fail``)."""
    report = ImportReport()
    for draft in drafts:
        missing = draft.missing_identity()
        if missing:
            reason = "missing identity: " + ", ".join(missing)
            report.skipped.append((draft, reason))
            _emit(on_event, "skip", draft, reason)
            continue

        try:
            rec = client.create_catalog_record(source=source, fields=draft.fields)
        except HTTPError as e:
            if e.status == 409:                      # natural-key duplicate (M2)
                report.skipped.append((draft, "already exists (natural-key 409)"))
                _emit(on_event, "skip", draft, "already exists")
            else:
                report.failed.append((draft, e))
                _emit(on_event, "fail", draft, e)
            continue
        except SmoothClientError as e:
            report.failed.append((draft, e))
            _emit(on_event, "fail", draft, e)
            continue

        rid = (rec.get("internal") or {}).get("id")
        report.created.append((draft, rec))
        _emit(on_event, "create", draft, rid)

        if preserve and rid:
            try:
                client.sync_client_section(
                    "tool-catalog-records", rid, client_name,
                    data={"format": draft.source_format,
                          "class": draft.source_class,
                          "properties": draft.raw})
            except SmoothClientError as e:
                report.preserve_failed.append((draft, e))
                _emit(on_event, "preserve_fail", draft, e)

    return report


def _emit(cb, kind, draft, info):
    if cb is not None:
        cb(kind, draft, info)

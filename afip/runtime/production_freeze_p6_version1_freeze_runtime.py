"""Production Freeze P6 runtime wrapper for Version 1 final freeze."""

from __future__ import annotations

from typing import Any, Mapping

from afip.version1_production_freeze import Version1FreezeRuntime


def run_production_freeze_p6_version1_freeze(record: Mapping[str, Any]) -> dict[str, object]:
    """Return a deterministic final production freeze report for a single record."""
    return Version1FreezeRuntime().explain_one(record).as_dict()

"""Read-only dashboard enrichment through the AFIP dashboard data contract."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
from afip.dashboard_data_contract import build_dashboard_contract


def enrich_profiles(profiles: list[Mapping[str, Any]], root: str | Path = ".") -> list[dict[str, Any]]:
    contract = build_dashboard_contract(root)
    supplied = {str(row.get("profile_id", "")).upper(): dict(row) for row in profiles}
    output: list[dict[str, Any]] = []
    for row in contract.get("profiles", ()):
        if not isinstance(row, Mapping):
            continue
        supplied_row = supplied.get(str(row.get("profile_id", "")).upper(), {})
        if supplied_row and not supplied_row.get("dashboard_data_source"):
            # Preserve legacy/test callers that intentionally supply a complete
            # profile snapshot. Production builds pass contract-tagged rows.
            merged = dict(row)
            merged.update(dict(supplied_row))
        else:
            merged = dict(supplied_row)
            merged.update(dict(row))
        output.append(merged)
    return output

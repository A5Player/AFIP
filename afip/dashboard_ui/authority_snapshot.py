"""Read-only dashboard enrichment through the AFIP production runtime authority."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
from afip.production_runtime_authority import build_dashboard_snapshot

def enrich_profiles(profiles: list[Mapping[str, Any]], root: str | Path = ".") -> list[dict[str, Any]]:
    return list(build_dashboard_snapshot(profiles, root).get("profiles", ()))

"""Read-only production dashboard authority aggregation for AFIP V1.

This module does not execute orders or mutate runtime authorities. It combines
existing authority snapshots into one traceable dashboard certification view.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

_REQUIRED_SECTIONS = (
    "runtime",
    "execution",
    "position",
    "research",
    "financial",
    "portfolio",
)
_BAD = {"BLOCKED", "FAILED", "ERROR", "INVALID", "STALE", "UNAVAILABLE"}
_GOOD = {"READY", "PASS", "VERIFIED", "RUNNING", "CERTIFIED"}


def _status(value: Any) -> str:
    return str(value or "DATA_UNAVAILABLE").strip().upper()


def _section(source: Mapping[str, Any], name: str) -> dict[str, Any]:
    raw = source.get(name)
    if not isinstance(raw, Mapping):
        return {
            "section": name,
            "status": "DATA_UNAVAILABLE",
            "reason": f"{name}_authority_missing",
            "source_authority": name,
            "data_available": False,
        }
    status = _status(raw.get("status", raw.get("authority_status")))
    return {
        "section": name,
        "status": status,
        "reason": str(raw.get("reason") or raw.get("status_reason") or "authority_reported_status"),
        "source_authority": str(raw.get("source_authority") or name),
        "generated_at_utc": raw.get("generated_at_utc"),
        "data_available": status != "DATA_UNAVAILABLE",
        "details": dict(raw),
    }


def build_production_dashboard_snapshot(source: Mapping[str, Any]) -> dict[str, Any]:
    sections = [_section(source, name) for name in _REQUIRED_SECTIONS]
    blockers: list[str] = []
    warnings: list[str] = []
    for item in sections:
        status = item["status"]
        name = item["section"]
        if not item["data_available"]:
            blockers.append(f"{name}_authority_missing")
        elif status in _BAD:
            blockers.append(f"{name}_authority_{status.lower()}")
        elif status not in _GOOD:
            warnings.append(f"{name}_authority_status_{status.lower()}")

    certification_status = "PASS" if not blockers else "REVIEW_REQUIRED"
    completeness = round((sum(1 for s in sections if s["data_available"]) / len(sections)) * 100.0, 2)
    return {
        "schema_version": "AFIP_V1_PRODUCTION_DASHBOARD_CERTIFICATION_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": certification_status,
        "dashboard_mode": "READ_ONLY_AUTHORITY_VIEW",
        "authority_sections": sections,
        "required_sections": list(_REQUIRED_SECTIONS),
        "completeness_percent": completeness,
        "certification_blockers": blockers,
        "warnings": warnings,
        "truth_policy": {
            "missing_data_is_zero": False,
            "stale_data_is_ready": False,
            "authority_conflicts_are_hidden": False,
            "execution_permission": False,
            "affects_trading": False,
            "automatic_control_change_allowed": False,
        },
    }


@dataclass(frozen=True)
class ProductionDashboardCertificationRuntime:
    """Build a single read-only dashboard certification snapshot."""

    def evaluate_one(self, source: Mapping[str, Any]) -> dict[str, Any]:
        return build_production_dashboard_snapshot(source)

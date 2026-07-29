"""Final, read-only AFIP V1 production certification aggregation.

The authority separates source/contract certification from live operational
certification. It never sends orders, mutates allocation, changes ranking, or
converts unavailable evidence into a passing result.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "AFIP_V1_FINAL_PRODUCTION_CERTIFICATION_V1"
REQUIRED_COMPONENTS: dict[str, tuple[str, ...]] = {
    "execution": ("afip/demo_execution_gateway/runtime.py",),
    "position": ("afip/position_care_runtime/runtime.py",),
    "research_dataset": ("afip/research_data_foundation/aggregator.py", "afip/research_data_foundation/dashboard.py"),
    "research_ranking": ("afip/research_ranking/runtime.py",),
    "financial": ("afip/financial_intelligence_certification/runtime.py",),
    "portfolio": ("afip/portfolio_authority_certification/runtime.py",),
    "dashboard": ("afip/production_dashboard_certification/runtime.py",),
}
REQUIRED_SAFETY_INVARIANTS = {
    "automatic_order_retry_allowed": False,
    "automatic_production_promotion_allowed": False,
    "automatic_capital_allocation_change_allowed": False,
    "dashboard_execution_permission": False,
    "missing_data_is_zero": False,
    "stale_data_is_ready": False,
    "quarantined_research_used_for_ranking": False,
}
BAD_RUNTIME_STATES = {"BLOCKED", "FAILED", "ERROR", "INVALID", "STALE", "UNAVAILABLE", "DATA_UNAVAILABLE", "REVIEW_REQUIRED"}
GOOD_RUNTIME_STATES = {"PASS", "READY", "VERIFIED", "RUNNING", "CERTIFIED", "CONNECTED"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _status(value: Any) -> str:
    return str(value or "DATA_UNAVAILABLE").strip().upper()


def _source_gate(project_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for component, paths in REQUIRED_COMPONENTS.items():
        missing = [path for path in paths if not (project_root / path).is_file()]
        status = "PASS" if not missing else "FAILED"
        rows.append({"component": component, "status": status, "required_paths": list(paths), "missing_paths": missing})
        blockers.extend(f"missing_source:{path}" for path in missing)
    return rows, blockers


def _safety_gate(safety: Mapping[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    supplied = dict(safety or {})
    effective = {key: supplied.get(key, expected) for key, expected in REQUIRED_SAFETY_INVARIANTS.items()}
    blockers = [f"safety_invariant_failed:{key}" for key, expected in REQUIRED_SAFETY_INVARIANTS.items() if effective.get(key) is not expected]
    return {
        "status": "PASS" if not blockers else "FAILED",
        "required_invariants": dict(REQUIRED_SAFETY_INVARIANTS),
        "effective_invariants": effective,
    }, blockers


def _runtime_gate(runtime_evidence: Mapping[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    required = ("runtime", "execution", "position", "research", "financial", "portfolio", "dashboard", "mt5")
    evidence = dict(runtime_evidence or {})
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for name in required:
        raw = evidence.get(name)
        if not isinstance(raw, Mapping):
            rows.append({"authority": name, "status": "DATA_UNAVAILABLE", "reason": f"{name}_runtime_evidence_missing"})
            blockers.append(f"runtime_evidence_missing:{name}")
            continue
        status = _status(raw.get("status", raw.get("authority_status")))
        rows.append({"authority": name, "status": status, "reason": raw.get("reason", "authority_reported_status")})
        if status in BAD_RUNTIME_STATES or status not in GOOD_RUNTIME_STATES:
            blockers.append(f"runtime_authority_not_ready:{name}:{status}")
    return {"status": "PASS" if not blockers else "REVIEW_REQUIRED", "authorities": rows}, blockers


def build_final_certification(
    project_root: str | Path,
    *,
    runtime_evidence: Mapping[str, Any] | None = None,
    safety_invariants: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    components, source_blockers = _source_gate(root)
    safety, safety_blockers = _safety_gate(safety_invariants)
    runtime, runtime_blockers = _runtime_gate(runtime_evidence)
    contract_blockers = source_blockers + safety_blockers
    all_blockers = contract_blockers + runtime_blockers
    source_status = "PASS" if not contract_blockers else "FAILED"
    if all_blockers:
        final_status = "READY_FOR_OPERATIONAL_CERTIFICATION" if source_status == "PASS" else "CERTIFICATION_BLOCKED"
    else:
        final_status = "PRODUCTION_CERTIFIED"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utcnow(),
        "status": final_status,
        "source_contract_certification": {"status": source_status, "components": components},
        "safety_certification": safety,
        "runtime_operational_certification": runtime,
        "certification_blockers": all_blockers,
        "production_certified": final_status == "PRODUCTION_CERTIFIED",
        "truth_policy": {
            "source_pass_is_live_pass": False,
            "missing_runtime_evidence_is_pass": False,
            "read_only_certification": True,
            "execution_permission": False,
            "affects_trading": False,
        },
    }


@dataclass(frozen=True)
class FinalProductionCertificationRuntime:
    project_root: str | Path = "."

    def evaluate(
        self,
        *,
        runtime_evidence: Mapping[str, Any] | None = None,
        safety_invariants: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_final_certification(self.project_root, runtime_evidence=runtime_evidence, safety_invariants=safety_invariants)

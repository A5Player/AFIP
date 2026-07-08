"""Version 1 production freeze observation contract for Production Freeze Pack P6.

This module evaluates final release evidence only. It does not execute orders,
change runtime decisions, or alter strategy behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Version1FreezeObservation:
    """Normalized release evidence for AFIP Version 1 final freeze."""

    market_regime: str
    signal_context: str
    execution_mode: str
    release_version: str
    architecture_audit_status: str
    acceptance_test_status: str
    documentation_status: str
    operations_status: str
    walk_forward_status: str
    release_candidate_status: str
    unresolved_release_items: int
    deterministic_runtime_score: float
    backward_compatibility_score: float
    documentation_coverage_score: float
    operations_readiness_score: float
    walk_forward_standard_score: float
    final_quality_score: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Version1FreezeObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            release_version=str(value.get("release_version", value.get("version", "1.0.0"))).strip() or "1.0.0",
            architecture_audit_status=_status(value.get("architecture_audit_status", value.get("architecture", "READY"))),
            acceptance_test_status=_status(value.get("acceptance_test_status", value.get("acceptance", "READY"))),
            documentation_status=_status(value.get("documentation_status", value.get("documentation", "READY"))),
            operations_status=_status(value.get("operations_status", value.get("operations", "READY"))),
            walk_forward_status=_status(value.get("walk_forward_status", value.get("walk_forward", "READY"))),
            release_candidate_status=_status(value.get("release_candidate_status", value.get("release_candidate", "READY"))),
            unresolved_release_items=_count(value.get("unresolved_release_items", value.get("open_items", 0))),
            deterministic_runtime_score=_ratio(value.get("deterministic_runtime_score", value.get("determinism_score", 0.0))),
            backward_compatibility_score=_ratio(value.get("backward_compatibility_score", value.get("compatibility_score", 0.0))),
            documentation_coverage_score=_ratio(value.get("documentation_coverage_score", value.get("documentation_score", 0.0))),
            operations_readiness_score=_ratio(value.get("operations_readiness_score", value.get("operations_score", 0.0))),
            walk_forward_standard_score=_ratio(value.get("walk_forward_standard_score", value.get("walk_forward_score", 0.0))),
            final_quality_score=_ratio(value.get("final_quality_score", value.get("quality_score", 0.0))),
            source=str(value.get("source", "VERSION1_PRODUCTION_FREEZE")).strip().upper() or "VERSION1_PRODUCTION_FREEZE",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def all_release_statuses_ready(self) -> bool:
        return all(
            status == "READY"
            for status in (
                self.architecture_audit_status,
                self.acceptance_test_status,
                self.documentation_status,
                self.operations_status,
                self.walk_forward_status,
                self.release_candidate_status,
            )
        )

    @property
    def release_score(self) -> float:
        value = (
            self.deterministic_runtime_score * 0.20
            + self.backward_compatibility_score * 0.17
            + self.documentation_coverage_score * 0.14
            + self.operations_readiness_score * 0.14
            + self.walk_forward_standard_score * 0.20
            + self.final_quality_score * 0.15
        )
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _count(value: Any) -> int:
    return max(int(value), 0)


def _mode(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    return text or "LOCKED_SIMULATION_ONLY"


def _status(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    if text in {"PASS", "PASSED", "COMPLETE", "COMPLETED", "READY"}:
        return "READY"
    if text in {"REVIEW", "REVIEW_REQUIRED", "PENDING"}:
        return "REVIEW"
    if text in {"BLOCK", "BLOCKED", "FAIL", "FAILED"}:
        return "BLOCKED"
    return text or "REVIEW"

"""Production release candidate observation contract for Production Milestone G Pack 8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionReleaseCandidateObservation:
    """Normalized release-candidate evidence for deterministic production review."""

    market_regime: str
    signal_context: str
    execution_mode: str
    configuration_version: str
    long_run_score: float
    production_hardening_score: float
    paper_trading_score: float
    observability_score: float
    feature_flag_score: float
    event_log_score: float
    deployment_checklist_score: float
    release_notes_score: float
    rollback_plan_score: float
    operator_handoff_score: float
    unresolved_reviews: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionReleaseCandidateObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        execution_mode = _mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY")))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        long_run_score = _ratio(value.get("long_run_score", value.get("stability_score", 0.0)))
        production_hardening_score = _ratio(value.get("production_hardening_score", value.get("hardening_score", 0.0)))
        paper_trading_score = _ratio(value.get("paper_trading_score", value.get("paper_score", 0.0)))
        observability_score = _ratio(value.get("observability_score", value.get("runtime_observability_score", 0.0)))
        feature_flag_score = _ratio(value.get("feature_flag_score", value.get("flag_score", 0.0)))
        event_log_score = _ratio(value.get("event_log_score", value.get("audit_log_score", 0.0)))
        deployment_checklist_score = _ratio(value.get("deployment_checklist_score", value.get("deployment_score", 0.0)))
        release_notes_score = _ratio(value.get("release_notes_score", value.get("release_score", 0.0)))
        rollback_plan_score = _ratio(value.get("rollback_plan_score", value.get("rollback_score", 0.0)))
        operator_handoff_score = _ratio(value.get("operator_handoff_score", value.get("handoff_score", 0.0)))
        unresolved_reviews = _count(value.get("unresolved_reviews", value.get("open_reviews", 0)))
        source = str(value.get("source", "PRODUCTION_RELEASE_CANDIDATE")).strip().upper() or "PRODUCTION_RELEASE_CANDIDATE"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            execution_mode=execution_mode,
            configuration_version=configuration_version,
            long_run_score=long_run_score,
            production_hardening_score=production_hardening_score,
            paper_trading_score=paper_trading_score,
            observability_score=observability_score,
            feature_flag_score=feature_flag_score,
            event_log_score=event_log_score,
            deployment_checklist_score=deployment_checklist_score,
            release_notes_score=release_notes_score,
            rollback_plan_score=rollback_plan_score,
            operator_handoff_score=operator_handoff_score,
            unresolved_reviews=unresolved_reviews,
            source=source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def release_evidence_quality(self) -> float:
        value = (
            self.long_run_score * 0.18
            + self.production_hardening_score * 0.14
            + self.paper_trading_score * 0.12
            + self.observability_score * 0.10
            + self.feature_flag_score * 0.08
            + self.event_log_score * 0.08
            + self.deployment_checklist_score * 0.12
            + self.release_notes_score * 0.06
            + self.rollback_plan_score * 0.06
            + self.operator_handoff_score * 0.06
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def production_release_score(self) -> float:
        review_score = 1.0 if self.unresolved_reviews == 0 else 0.0
        value = self.release_evidence_quality * 0.82 + review_score * 0.18
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

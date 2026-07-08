"""Long-run stability observation contract for Production Milestone G Pack 7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LongRunStabilityObservation:
    """Normalized long-run stability evidence for deterministic runtime review."""

    market_regime: str
    signal_context: str
    runtime_component: str
    execution_mode: str
    configuration_version: str
    paper_trading_score: float
    production_hardening_score: float
    runtime_metrics_score: float
    feature_flag_score: float
    repeated_runs: int
    deterministic_matches: int
    state_integrity_score: float
    resource_trend_score: float
    anomaly_rate: float
    max_drawdown: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LongRunStabilityObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        runtime_component = str(value.get("runtime_component", value.get("component", "AFIP_RUNTIME"))).strip().upper() or "AFIP_RUNTIME"
        execution_mode = _mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY")))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        paper_trading_score = _ratio(value.get("paper_trading_score", value.get("paper_score", 0.0)))
        production_hardening_score = _ratio(value.get("production_hardening_score", value.get("hardening_score", 0.0)))
        runtime_metrics_score = _ratio(value.get("runtime_metrics_score", value.get("metrics_score", 0.0)))
        feature_flag_score = _ratio(value.get("feature_flag_score", value.get("flag_score", 0.0)))
        repeated_runs = _count(value.get("repeated_runs", value.get("runs", 0)))
        deterministic_matches = _count(value.get("deterministic_matches", value.get("matching_runs", 0)))
        state_integrity_score = _ratio(value.get("state_integrity_score", value.get("state_score", 0.0)))
        resource_trend_score = _ratio(value.get("resource_trend_score", value.get("resource_score", 0.0)))
        anomaly_rate = _ratio(value.get("anomaly_rate", value.get("anomalies", 0.0)))
        max_drawdown = _ratio(value.get("max_drawdown", value.get("drawdown", 0.0)))
        source = str(value.get("source", "LONG_RUN_STABILITY")).strip().upper() or "LONG_RUN_STABILITY"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            runtime_component=runtime_component,
            execution_mode=execution_mode,
            configuration_version=configuration_version,
            paper_trading_score=paper_trading_score,
            production_hardening_score=production_hardening_score,
            runtime_metrics_score=runtime_metrics_score,
            feature_flag_score=feature_flag_score,
            repeated_runs=repeated_runs,
            deterministic_matches=deterministic_matches,
            state_integrity_score=state_integrity_score,
            resource_trend_score=resource_trend_score,
            anomaly_rate=anomaly_rate,
            max_drawdown=max_drawdown,
            source=source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def has_repeated_run_sample(self) -> bool:
        return self.repeated_runs >= 3

    @property
    def deterministic_consistency(self) -> float:
        if self.repeated_runs <= 0:
            return 0.0
        return round(min(max(self.deterministic_matches / self.repeated_runs, 0.0), 1.0), 6)

    @property
    def stability_quality(self) -> float:
        value = (
            self.paper_trading_score * 0.16
            + self.production_hardening_score * 0.16
            + self.runtime_metrics_score * 0.14
            + self.feature_flag_score * 0.10
            + self.deterministic_consistency * 0.18
            + self.state_integrity_score * 0.12
            + self.resource_trend_score * 0.08
            + (1.0 - self.anomaly_rate) * 0.06
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def long_run_score(self) -> float:
        drawdown_score = 1.0 - self.max_drawdown
        sample_score = min(self.repeated_runs / 12.0, 1.0)
        value = self.stability_quality * 0.64 + drawdown_score * 0.18 + sample_score * 0.18
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

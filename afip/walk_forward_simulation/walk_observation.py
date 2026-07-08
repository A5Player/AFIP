"""Walk-forward historical paper simulation observation contract for Production Freeze Pack P5.

This module intentionally evaluates only historical paper-simulation evidence.
It does not execute live orders and it does not change trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class WalkForwardObservation:
    """Normalized evidence for no-lookahead historical paper simulation."""

    market_regime: str
    signal_context: str
    execution_mode: str
    historical_window_bars: int
    warmup_bars: int
    revealed_future_bars: int
    simulated_orders: int
    completed_orders: int
    baseline_win_rate: float
    baseline_expectancy: float
    max_drawdown_percent: float
    spread_filter_score: float
    regime_coverage_score: float
    standard_quality_score: float
    unresolved_simulation_items: int
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "WalkForwardObservation":
        return cls(
            market_regime=str(value.get("market_regime", "")).strip().upper(),
            signal_context=str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN",
            execution_mode=_mode(value.get("execution_mode", value.get("mode", "LOCKED_SIMULATION_ONLY"))),
            historical_window_bars=_count(value.get("historical_window_bars", value.get("window_bars", 0))),
            warmup_bars=_count(value.get("warmup_bars", value.get("warmup", 0))),
            revealed_future_bars=_count(value.get("revealed_future_bars", value.get("lookahead_bars", 0))),
            simulated_orders=_count(value.get("simulated_orders", value.get("paper_orders", 0))),
            completed_orders=_count(value.get("completed_orders", value.get("closed_orders", 0))),
            baseline_win_rate=_ratio(value.get("baseline_win_rate", value.get("win_rate", 0.0))),
            baseline_expectancy=_expectancy(value.get("baseline_expectancy", value.get("expectancy", 0.0))),
            max_drawdown_percent=_ratio(value.get("max_drawdown_percent", value.get("drawdown", 0.0))),
            spread_filter_score=_ratio(value.get("spread_filter_score", value.get("spread_score", 0.0))),
            regime_coverage_score=_ratio(value.get("regime_coverage_score", value.get("coverage_score", 0.0))),
            standard_quality_score=_ratio(value.get("standard_quality_score", value.get("quality_score", 0.0))),
            unresolved_simulation_items=_count(value.get("unresolved_simulation_items", value.get("open_items", 0))),
            source=str(value.get("source", "WALK_FORWARD_HISTORICAL_PAPER_SIMULATION")).strip().upper()
            or "WALK_FORWARD_HISTORICAL_PAPER_SIMULATION",
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def has_no_lookahead(self) -> bool:
        return self.revealed_future_bars == 0

    @property
    def has_enough_history(self) -> bool:
        return self.historical_window_bars > self.warmup_bars and self.warmup_bars > 0

    @property
    def completion_score(self) -> float:
        if self.simulated_orders <= 0:
            return 0.0
        return round(min(max(self.completed_orders / self.simulated_orders, 0.0), 1.0), 6)

    @property
    def drawdown_control_score(self) -> float:
        # Lower drawdown is better; cap penalty at 30% drawdown.
        penalty = min(self.max_drawdown_percent / 0.30, 1.0)
        return round(1.0 - penalty, 6)

    @property
    def expectancy_score(self) -> float:
        # Map expectancy in [-1, +1] into [0, 1].
        return round(min(max((self.baseline_expectancy + 1.0) / 2.0, 0.0), 1.0), 6)

    @property
    def acceptance_score(self) -> float:
        value = (
            self.completion_score * 0.18
            + self.baseline_win_rate * 0.16
            + self.expectancy_score * 0.18
            + self.drawdown_control_score * 0.14
            + self.spread_filter_score * 0.12
            + self.regime_coverage_score * 0.12
            + self.standard_quality_score * 0.10
        )
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _expectancy(value: Any) -> float:
    return min(max(float(value), -1.0), 1.0)


def _count(value: Any) -> int:
    return max(int(value), 0)


def _mode(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    return text or "LOCKED_SIMULATION_ONLY"

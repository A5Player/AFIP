"""Walk-forward historical paper simulation profile for Production Freeze Pack P5."""

from __future__ import annotations

from dataclasses import dataclass

from .walk_observation import WalkForwardObservation


@dataclass(frozen=True)
class WalkForwardProfile:
    """Deterministic profile for no-lookahead historical paper simulation."""

    market_regime: str
    signal_context: str
    status: str
    reason: str
    historical_window_bars: int
    warmup_bars: int
    simulated_orders: int
    completed_orders: int
    completion_score: float
    baseline_win_rate: float
    expectancy_score: float
    drawdown_control_score: float
    acceptance_score: float
    unresolved_simulation_items: int
    source: str

    @classmethod
    def from_observation(cls, observation: WalkForwardObservation, *, status: str, reason: str) -> "WalkForwardProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            status=status,
            reason=reason,
            historical_window_bars=observation.historical_window_bars,
            warmup_bars=observation.warmup_bars,
            simulated_orders=observation.simulated_orders,
            completed_orders=observation.completed_orders,
            completion_score=observation.completion_score,
            baseline_win_rate=observation.baseline_win_rate,
            expectancy_score=observation.expectancy_score,
            drawdown_control_score=observation.drawdown_control_score,
            acceptance_score=observation.acceptance_score,
            unresolved_simulation_items=observation.unresolved_simulation_items,
            source=observation.source,
        )

    @property
    def simulation_gate(self) -> str:
        if self.status == "READY":
            return "WALK_FORWARD_STANDARD_READY"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "BLOCKED"

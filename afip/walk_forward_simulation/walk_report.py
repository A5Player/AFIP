"""Walk-forward historical paper simulation report for Production Freeze Pack P5."""

from __future__ import annotations

from dataclasses import asdict

from .walk_profile import WalkForwardProfile


class WalkForwardReport:
    """Human-readable report for no-lookahead historical paper simulation."""

    def __init__(self, profile: WalkForwardProfile) -> None:
        self.profile = profile

    def as_dict(self) -> dict[str, object]:
        data = asdict(self.profile)
        data["simulation_gate"] = self.profile.simulation_gate
        data["no_lookahead_standard"] = True
        return data

    def as_text(self) -> str:
        return (
            "Walk-Forward Historical Paper Simulation Report\n"
            f"Status: {self.profile.status}\n"
            f"Gate: {self.profile.simulation_gate}\n"
            f"Market regime: {self.profile.market_regime}\n"
            f"Signal context: {self.profile.signal_context}\n"
            f"Historical bars: {self.profile.historical_window_bars}\n"
            f"Simulated orders: {self.profile.simulated_orders}\n"
            f"Completed orders: {self.profile.completed_orders}\n"
            f"Acceptance score: {self.profile.acceptance_score:.4f}\n"
            f"Decision reason: {self.profile.reason}"
        )

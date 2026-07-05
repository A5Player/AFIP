"""Exposure engine for account and portfolio exposure control."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class ExposureEngine:
    """Evaluate open position exposure against account equity."""

    name = "ExposureEngine"

    def __init__(self, max_exposure_percent: float = 35.0):
        self.max_exposure_percent = max(1.0, float(max_exposure_percent))

    def evaluate(self, snapshot: dict) -> dict:
        equity = float(snapshot.get("equity", 0.0) or 0.0)
        exposure = float(snapshot.get("open_exposure", 0.0) or 0.0)
        if equity <= 0:
            return EngineResult(self.name, "BLOCKED", "WAIT", 0.0, "equity_not_available", {}).as_dict()
        exposure_percent = exposure / equity * 100.0
        remaining_percent = max(0.0, self.max_exposure_percent - exposure_percent)
        allowed = exposure_percent <= self.max_exposure_percent
        confidence = clamp(100.0 - exposure_percent / self.max_exposure_percent * 100.0)
        return EngineResult(
            self.name,
            "READY" if allowed else "BLOCKED",
            "ALLOW" if allowed else "WAIT",
            confidence,
            "exposure_within_limit" if allowed else "exposure_limit_reached",
            {
                "equity": round(equity, 2),
                "open_exposure": round(exposure, 2),
                "exposure_percent": round(exposure_percent, 2),
                "remaining_exposure_percent": round(remaining_percent, 2),
                "max_exposure_percent": round(self.max_exposure_percent, 2),
            },
        ).as_dict()

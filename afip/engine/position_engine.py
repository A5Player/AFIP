"""Position engine for lot sizing and protective distance calculation."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class PositionEngine:
    """Calculate conservative position sizing from risk budget and stop distance."""

    name = "PositionEngine"

    def __init__(self, min_lot: float = 0.01, max_lot: float = 0.10, lot_step: float = 0.01):
        self.min_lot = max(0.01, float(min_lot))
        self.max_lot = max(self.min_lot, float(max_lot))
        self.lot_step = max(0.01, float(lot_step))

    def evaluate(self, snapshot: dict) -> dict:
        equity = float(snapshot.get("equity", 0.0) or 0.0)
        risk_percent = float(snapshot.get("risk_percent", 1.0) or 1.0)
        stop_points = float(snapshot.get("stop_points", 900.0) or 900.0)
        point_value = float(snapshot.get("point_value_per_lot", 1.0) or 1.0)
        if equity <= 0 or stop_points <= 0 or point_value <= 0:
            return EngineResult(self.name, "LEARNING", "WAIT", 30.0, "position_inputs_not_available", {}).as_dict()
        risk_amount = equity * risk_percent / 100.0
        raw_lot = risk_amount / (stop_points * point_value)
        lot = self._round_lot(raw_lot)
        confidence = clamp(70.0 + min(25.0, equity / 1000.0 * 5.0)) if lot >= self.min_lot else 40.0
        return EngineResult(
            self.name,
            "READY",
            "ALLOW" if lot >= self.min_lot else "WAIT",
            confidence,
            "position_size_ready" if lot >= self.min_lot else "position_size_below_minimum",
            {
                "risk_amount": round(risk_amount, 2),
                "risk_percent": round(risk_percent, 2),
                "stop_points": round(stop_points, 2),
                "suggested_lot": round(lot, 2),
                "raw_lot": round(raw_lot, 4),
            },
        ).as_dict()

    def _round_lot(self, raw_lot: float) -> float:
        clipped = max(self.min_lot, min(self.max_lot, float(raw_lot)))
        steps = int(clipped / self.lot_step)
        return round(max(self.min_lot, steps * self.lot_step), 2)

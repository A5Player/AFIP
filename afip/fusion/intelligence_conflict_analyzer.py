from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class IntelligenceConflictAnalysisResult:
    status: str
    conflict_level: str
    dominant_direction: str
    buy_pressure: float
    sell_pressure: float
    flat_pressure: float
    conflict_ratio: float
    reason: str


class IntelligenceConflictAnalyzer:
    """Evaluate directional disagreement across financial intelligence inputs."""

    VALID_DIRECTIONS = {"BUY", "SELL", "FLAT"}

    def analyze(self, intelligence_inputs: Iterable[Mapping[str, object]] | None = None) -> IntelligenceConflictAnalysisResult:
        inputs = list(intelligence_inputs or [])
        if not inputs:
            return IntelligenceConflictAnalysisResult(
                status="CONFLICT_ANALYSIS_READY",
                conflict_level="LOW",
                dominant_direction="FLAT",
                buy_pressure=0.0,
                sell_pressure=0.0,
                flat_pressure=1.0,
                conflict_ratio=0.0,
                reason="no_active_directional_pressure",
            )

        pressure = {"BUY": 0.0, "SELL": 0.0, "FLAT": 0.0}
        for item in inputs:
            direction = str(item.get("direction", "FLAT")).upper()
            if direction not in self.VALID_DIRECTIONS:
                direction = "FLAT"
            confidence = self._normalize_float(item.get("confidence", 0.0))
            weight = self._normalize_weight(item.get("weight", 1.0))
            pressure[direction] += confidence * weight

        total_pressure = sum(pressure.values())
        if total_pressure <= 0.0:
            normalized = {"BUY": 0.0, "SELL": 0.0, "FLAT": 1.0}
        else:
            normalized = {key: value / total_pressure for key, value in pressure.items()}

        dominant_direction = max(normalized, key=normalized.get)
        opposing_direction = "SELL" if dominant_direction == "BUY" else "BUY"
        conflict_ratio = normalized[opposing_direction] if dominant_direction in {"BUY", "SELL"} else max(normalized["BUY"], normalized["SELL"])
        conflict_level = self._level(conflict_ratio)
        reason = self._reason(dominant_direction, conflict_level)

        return IntelligenceConflictAnalysisResult(
            status="CONFLICT_ANALYSIS_READY",
            conflict_level=conflict_level,
            dominant_direction=dominant_direction,
            buy_pressure=round(normalized["BUY"], 4),
            sell_pressure=round(normalized["SELL"], 4),
            flat_pressure=round(normalized["FLAT"], 4),
            conflict_ratio=round(conflict_ratio, 4),
            reason=reason,
        )

    @staticmethod
    def _normalize_float(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))

    @staticmethod
    def _normalize_weight(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 1.0
        return max(0.0, number)

    @staticmethod
    def _level(conflict_ratio: float) -> str:
        if conflict_ratio >= 0.42:
            return "HIGH"
        if conflict_ratio >= 0.24:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _reason(direction: str, level: str) -> str:
        if direction == "FLAT":
            return "neutral_directional_pressure"
        if level == "HIGH":
            return "material_directional_conflict"
        if level == "MODERATE":
            return "controlled_directional_conflict"
        return "dominant_directional_alignment"

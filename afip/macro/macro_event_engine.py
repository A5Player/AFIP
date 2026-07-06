"""Macro event impact scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MacroEventAssessment:
    """Macro event impact assessment for gold exposure review."""

    event_name: str
    impact_score: float
    urgency_score: float
    confidence_score: float
    gold_bias: str
    reason: str


class MacroEventEngine:
    """Score macro event importance, urgency, and expected gold sensitivity."""

    BASE_EVENT_IMPACT = {
        "FOMC": 100.0,
        "FED_RATE_DECISION": 100.0,
        "FED_CHAIR_SPEECH": 95.0,
        "CPI": 98.0,
        "CORE_CPI": 96.0,
        "PCE": 94.0,
        "CORE_PCE": 94.0,
        "NFP": 92.0,
        "NONFARM_PAYROLLS": 92.0,
        "JOBLESS_CLAIMS": 72.0,
        "GDP": 70.0,
        "PPI": 68.0,
        "RETAIL_SALES": 65.0,
        "ISM": 58.0,
        "PMI": 54.0,
    }

    def assess(self, calendar_state: Mapping[str, object]) -> MacroEventAssessment:
        event_name = str(calendar_state.get("next_event") or "NO_SCHEDULED_EVENT")
        normalized = event_name.upper().replace(" ", "_").replace("-", "_")
        minutes = self._to_float(calendar_state.get("minutes_to_event"), default=9999.0)
        base_impact = self.BASE_EVENT_IMPACT.get(normalized, 25.0)
        urgency = self._urgency_from_minutes(minutes)
        confidence = min(100.0, max(0.0, (base_impact * 0.65) + (urgency * 0.35)))
        if base_impact >= 90.0 and urgency >= 80.0:
            gold_bias = "VOLATILITY_RISK"
            reason = "high_impact_macro_event_window"
        elif base_impact >= 70.0:
            gold_bias = "MACRO_SENSITIVE"
            reason = "important_macro_event_scheduled"
        else:
            gold_bias = "NEUTRAL"
            reason = "low_macro_event_pressure"
        return MacroEventAssessment(event_name, round(base_impact, 2), round(urgency, 2), round(confidence, 2), gold_bias, reason)

    def assess_dict(self, calendar_state: Mapping[str, object]) -> dict[str, object]:
        result = self.assess(calendar_state)
        return {
            "event_name": result.event_name,
            "impact_score": result.impact_score,
            "urgency_score": result.urgency_score,
            "confidence_score": result.confidence_score,
            "gold_bias": result.gold_bias,
            "reason": result.reason,
        }

    def _urgency_from_minutes(self, minutes: float) -> float:
        absolute_minutes = abs(minutes)
        if -15.0 <= minutes <= 30.0:
            return 100.0
        if absolute_minutes <= 60.0:
            return 80.0
        if absolute_minutes <= 180.0:
            return 50.0
        return 15.0

    def _to_float(self, value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

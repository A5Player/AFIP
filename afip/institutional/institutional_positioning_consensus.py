"""Institutional positioning consensus for gold market context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class InstitutionalPositioningConsensus:
    """Integrated institutional positioning assessment."""

    status: str
    positioning_bias: str
    confidence_score: float
    institutional_score: float
    component_scores: Mapping[str, float]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "positioning_bias": self.positioning_bias,
            "confidence_score": self.confidence_score,
            "institutional_score": self.institutional_score,
            "component_scores": dict(self.component_scores),
            "reason": self.reason,
        }


class InstitutionalPositioningConsensusEngine:
    """Combine COT, open interest, ETF flows, and COMEX inventory context."""

    def combine(
        self,
        cot_state: Mapping[str, object],
        open_interest_state: Mapping[str, object],
        etf_flow_state: Mapping[str, object],
        comex_state: Mapping[str, object],
    ) -> InstitutionalPositioningConsensus:
        cot_score = self._cot_score(cot_state)
        oi_score = self._open_interest_score(open_interest_state)
        etf_score = self._etf_score(etf_flow_state)
        comex_score = self._comex_score(comex_state)
        institutional_score = (cot_score * 0.36) + (oi_score * 0.28) + (etf_score * 0.22) + (comex_score * 0.14)
        institutional_score = round(min(100.0, max(0.0, institutional_score)), 2)
        component_scores = {
            "cot_positioning": round(cot_score, 2),
            "open_interest": round(oi_score, 2),
            "etf_gold_flow": round(etf_score, 2),
            "comex_inventory": round(comex_score, 2),
        }
        confidence = self._confidence(component_scores)
        bias = self._bias(institutional_score, component_scores)
        reason = self._reason(bias, component_scores)

        return InstitutionalPositioningConsensus(
            status="INSTITUTIONAL_POSITIONING_READY",
            positioning_bias=bias,
            confidence_score=confidence,
            institutional_score=institutional_score,
            component_scores=component_scores,
            reason=reason,
        )

    def combine_dict(
        self,
        cot_state: Mapping[str, object],
        open_interest_state: Mapping[str, object],
        etf_flow_state: Mapping[str, object],
        comex_state: Mapping[str, object],
    ) -> dict[str, object]:
        return self.combine(cot_state, open_interest_state, etf_flow_state, comex_state).as_dict()

    def _cot_score(self, state: Mapping[str, object]) -> float:
        bias = str(state.get("positioning_bias", "NEUTRAL"))
        confidence = self._to_float(state.get("confidence_score"), 0.0)
        return self._bias_score(bias, confidence)

    def _open_interest_score(self, state: Mapping[str, object]) -> float:
        value = str(state.get("participation_state", "PARTICIPATION_BALANCED"))
        confidence = self._to_float(state.get("confidence_score"), 0.0)
        if value in {"LONG_PARTICIPATION_EXPANDING", "SHORT_COVERING"}:
            return min(100.0, 50.0 + confidence * 0.45)
        if value in {"SHORT_PARTICIPATION_EXPANDING", "LONG_LIQUIDATION"}:
            return max(0.0, 50.0 - confidence * 0.45)
        return 50.0

    def _etf_score(self, state: Mapping[str, object]) -> float:
        return self._bias_score(str(state.get("flow_bias", "NEUTRAL")), self._to_float(state.get("confidence_score"), 0.0))

    def _comex_score(self, state: Mapping[str, object]) -> float:
        value = str(state.get("inventory_state", "INVENTORY_BALANCED"))
        confidence = self._to_float(state.get("confidence_score"), 0.0)
        if value == "AVAILABLE_SUPPLY_TIGHTENING":
            return min(100.0, 50.0 + confidence * 0.35)
        if value == "AVAILABLE_SUPPLY_EXPANDING":
            return max(0.0, 50.0 - confidence * 0.35)
        return 50.0

    def _bias_score(self, bias: str, confidence: float) -> float:
        if bias == "GOLD_SUPPORTIVE":
            return min(100.0, 50.0 + confidence * 0.45)
        if bias == "GOLD_PRESSURE":
            return max(0.0, 50.0 - confidence * 0.45)
        return 50.0

    def _confidence(self, scores: Mapping[str, float]) -> float:
        values = list(scores.values()) or [50.0]
        dispersion = max(values) - min(values)
        directional_strength = abs((sum(values) / len(values)) - 50.0)
        return round(min(98.0, max(35.0, 58.0 + directional_strength * 0.70 - dispersion * 0.20)), 2)

    def _bias(self, score: float, scores: Mapping[str, float]) -> str:
        if max(scores.values()) - min(scores.values()) >= 65.0:
            return "MIXED"
        if score >= 62.0:
            return "GOLD_SUPPORTIVE"
        if score <= 38.0:
            return "GOLD_PRESSURE"
        return "NEUTRAL"

    def _reason(self, bias: str, scores: Mapping[str, float]) -> str:
        if bias == "MIXED":
            return "institutional_inputs_conflicting"
        if bias == "GOLD_SUPPORTIVE":
            return "institutional_positioning_supportive_for_gold"
        if bias == "GOLD_PRESSURE":
            return "institutional_positioning_pressure_for_gold"
        return "institutional_positioning_neutral"

    @staticmethod
    def _to_float(value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

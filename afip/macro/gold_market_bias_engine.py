"""Gold market bias scoring from macro market factors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .dxy_runtime import DxyAssessment
from .real_yield_runtime import RealYieldAssessment
from .treasury_yield_runtime import TreasuryYieldAssessment


@dataclass(frozen=True)
class GoldMarketBias:
    """Gold market bias derived from macro factor assessments."""

    status: str
    bias: str
    score: float
    confidence: float
    supportive_count: int
    pressure_count: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "bias": self.bias,
            "score": self.score,
            "confidence": self.confidence,
            "supportive_count": self.supportive_count,
            "pressure_count": self.pressure_count,
            "reason": self.reason,
        }


class GoldMarketBiasEngine:
    """Aggregate DXY, Treasury, and real yield views into one gold bias."""

    def evaluate(
        self,
        dxy: DxyAssessment,
        treasury: TreasuryYieldAssessment,
        real_yield: RealYieldAssessment,
        additional_reasons: Iterable[str] | None = None,
    ) -> GoldMarketBias:
        assessments = (dxy, treasury, real_yield)
        score = 50.0
        supportive_count = 0
        pressure_count = 0
        reasons: list[str] = []
        weights = {
            "DXY_READY": 0.26,
            "TREASURY_YIELD_READY": 0.22,
            "REAL_YIELD_READY": 0.36,
        }
        for assessment in assessments:
            direction = getattr(assessment, "direction")
            pressure_score = float(getattr(assessment, "pressure_score"))
            weight = weights.get(getattr(assessment, "status"), 0.16)
            magnitude = (pressure_score - 50.0) * weight
            if direction == "GOLD_SUPPORTIVE":
                score += magnitude
                supportive_count += 1
                reasons.append(str(getattr(assessment, "reason")))
            elif direction == "GOLD_PRESSURE":
                score -= magnitude
                pressure_count += 1
                reasons.append(str(getattr(assessment, "reason")))
        if additional_reasons:
            reasons.extend([reason for reason in additional_reasons if reason])
        score = round(min(100.0, max(0.0, score)), 2)
        confidence = round(min(100.0, 45.0 + abs(score - 50.0) * 1.35 + (supportive_count + pressure_count) * 6.0), 2)
        if supportive_count and pressure_count and abs(score - 50.0) < 10.0:
            bias = "REVIEW"
            reason = "mixed_macro_market_factors"
        elif score >= 62.0:
            bias = "GOLD_SUPPORTIVE"
            reason = "+".join(reasons) if reasons else "macro_market_supportive"
        elif score <= 38.0:
            bias = "GOLD_PRESSURE"
            reason = "+".join(reasons) if reasons else "macro_market_pressure"
        else:
            bias = "NEUTRAL"
            reason = "+".join(reasons) if reasons else "macro_market_balanced"
        return GoldMarketBias("GOLD_MARKET_BIAS_READY", bias, score, confidence, supportive_count, pressure_count, reason)

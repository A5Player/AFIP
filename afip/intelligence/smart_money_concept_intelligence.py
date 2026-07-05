"""AFIP Smart Money Concept Integration.

Combines institutional market structure signals into one directional bias.
"""
from __future__ import annotations

from afip.intelligence.fair_value_gap_intelligence import FairValueGapIntelligence
from afip.intelligence.imbalance_intelligence import ImbalanceIntelligence
from afip.intelligence.liquidity_sweep_intelligence import LiquiditySweepIntelligence
from afip.intelligence.order_block_intelligence import OrderBlockIntelligence


class SmartMoneyConceptIntelligence:
    """Integrate FVG, imbalance, order block, and liquidity sweep intelligence."""

    name = "SmartMoneyConceptIntelligence"

    def __init__(self):
        self.components = (
            FairValueGapIntelligence(),
            ImbalanceIntelligence(),
            OrderBlockIntelligence(),
            LiquiditySweepIntelligence(),
        )

    def analyze(self, snapshot: dict) -> dict:
        component_results = [component.analyze(snapshot) for component in self.components]
        buy_score = self._weighted_score(component_results, "buy_score")
        sell_score = self._weighted_score(component_results, "sell_score")
        difference = abs(buy_score - sell_score)

        direction = "FLAT"
        institutional_bias = "BALANCED"
        confidence = 45.0
        if buy_score > sell_score and difference >= 8.0:
            direction = "BUY"
            institutional_bias = "BULLISH_SMART_MONEY_BIAS"
            confidence = min(95.0, 50.0 + difference * 0.6 + buy_score * 0.25)
        elif sell_score > buy_score and difference >= 8.0:
            direction = "SELL"
            institutional_bias = "BEARISH_SMART_MONEY_BIAS"
            confidence = min(95.0, 50.0 + difference * 0.6 + sell_score * 0.25)

        alignment_count = sum(1 for result in component_results if result.get("direction") == direction and direction != "FLAT")
        if direction != "FLAT":
            confidence = min(96.0, confidence + alignment_count * 3.0)

        return {
            "name": self.name,
            "status": "READY",
            "direction": direction,
            "confidence": round(confidence, 2),
            "reason": "smart_money_concept_integration_evaluated",
            "institutional_bias": institutional_bias,
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "alignment_count": alignment_count,
            "components": component_results,
        }

    @staticmethod
    def _weighted_score(results: list[dict], score_key: str) -> float:
        weights = {
            "FairValueGapIntelligence": 0.24,
            "ImbalanceIntelligence": 0.18,
            "OrderBlockIntelligence": 0.28,
            "LiquiditySweepIntelligence": 0.30,
        }
        score = 0.0
        for result in results:
            score += float(result.get(score_key, 0.0) or 0.0) * weights.get(str(result.get("name")), 0.0)
        return score

"""Institutional score engine for AFIP.

Combines fair value gap, imbalance, order block, liquidity sweep, and smart
money concept signals into a financial institutional bias score.
"""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp, direction_scores


class InstitutionalScoreEngine:
    """Aggregate institutional intelligence into a single bias payload."""

    name = "InstitutionalScoreEngine"

    institutional_names = {
        "FairValueGapIntelligence",
        "ImbalanceIntelligence",
        "OrderBlockIntelligence",
        "LiquiditySweepIntelligence",
        "SmartMoneyConceptIntelligence",
    }

    def evaluate(self, snapshot: dict) -> dict:
        intelligence = [
            item for item in snapshot.get("intelligence", [])
            if item.get("name") in self.institutional_names
        ]
        if not intelligence:
            return EngineResult(
                self.name,
                "LEARNING",
                "WAIT",
                35.0,
                "institutional_inputs_not_available",
                {"buy_score": 0.0, "sell_score": 0.0, "input_count": 0},
            ).as_dict()

        weighted_inputs = []
        for item in intelligence:
            copy = dict(item)
            copy["weight"] = self._weight(copy)
            weighted_inputs.append(copy)

        buy_score, sell_score, flat_score = direction_scores(weighted_inputs)
        edge = abs(buy_score - sell_score)
        dominant = max(buy_score, sell_score, flat_score)
        confidence = clamp(45.0 + dominant * 0.4 + edge * 0.35)
        action = "BUY" if buy_score > sell_score + 5 else "SELL" if sell_score > buy_score + 5 else "WAIT"
        reason = "institutional_buy_bias" if action == "BUY" else "institutional_sell_bias" if action == "SELL" else "institutional_bias_balanced"
        return EngineResult(
            self.name,
            "READY",
            action,
            confidence,
            reason,
            {
                "buy_score": round(buy_score, 2),
                "sell_score": round(sell_score, 2),
                "flat_score": round(flat_score, 2),
                "input_count": len(intelligence),
                "edge": round(edge, 2),
            },
        ).as_dict()

    @staticmethod
    def _weight(item: dict) -> float:
        name = item.get("name")
        if name == "SmartMoneyConceptIntelligence":
            return 1.6
        if name in {"OrderBlockIntelligence", "LiquiditySweepIntelligence"}:
            return 1.3
        return 1.0

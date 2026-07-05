class MultiTimeframeScoreCalculator:
    def calculate(self, trend_consensus: dict, market_regime: dict) -> dict:
        direction = trend_consensus.get("direction", "FLAT")
        base_confidence = float(trend_consensus.get("confidence", 0))
        regime = market_regime.get("regime", "UNKNOWN")

        risk_penalty = 0
        if regime == "EXPANSION":
            risk_penalty = 10
        elif regime == "UNKNOWN":
            risk_penalty = 25

        buy_score = max(0, base_confidence - risk_penalty) if direction == "BUY" else 0
        sell_score = max(0, base_confidence - risk_penalty) if direction == "SELL" else 0

        return {
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "overall_confidence": round(max(buy_score, sell_score), 2),
            "risk_penalty": risk_penalty,
            "regime": regime,
            "direction": direction,
            "reason": "multi_timeframe_score",
        }

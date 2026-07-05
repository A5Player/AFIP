from afip.risk.risk_profile import RiskProfile

class RiskAssessor:
    def __init__(self, profile=None):
        self.profile = profile or RiskProfile()

    def assess(self, snapshot: dict, score: dict, portfolio_state: dict | None = None) -> dict:
        portfolio_state = portfolio_state or {"open_positions": 0}
        reasons = []
        allowed = True

        spread = float(snapshot.get("spread", 999))
        confidence = float(score.get("overall_confidence", 0))
        regime_penalty = float(score.get("risk_penalty", score.get("penalties", 0)))
        open_positions = int(portfolio_state.get("open_positions", 0))

        if spread > self.profile.max_spread:
            allowed = False
            reasons.append("spread_too_high")

        if confidence < self.profile.min_confidence:
            allowed = False
            reasons.append("confidence_below_minimum")

        if regime_penalty > self.profile.max_regime_penalty:
            allowed = False
            reasons.append("regime_penalty_too_high")

        if open_positions >= self.profile.max_position_count:
            allowed = False
            reasons.append("position_limit_reached")

        return {
            "allowed": allowed,
            "risk_score": max(0, 100 - spread - regime_penalty),
            "reasons": reasons or ["risk_pass"],
            "profile": self.profile.__dict__,
        }

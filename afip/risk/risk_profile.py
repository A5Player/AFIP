from dataclasses import dataclass

@dataclass(frozen=True)
class RiskProfile:
    max_spread: float = 35.0
    min_confidence: float = 60.0
    max_regime_penalty: float = 25.0
    max_position_count: int = 1
    live_trading_enabled: bool = False

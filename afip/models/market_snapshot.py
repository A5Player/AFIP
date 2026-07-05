from dataclasses import dataclass
from typing import List

@dataclass
class MarketSnapshot:
    symbol: str
    closes: List[float]
    highs: List[float]
    lows: List[float]
    spread: float
    source: str = "SIMULATION"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "closes": self.closes,
            "highs": self.highs,
            "lows": self.lows,
            "spread": self.spread,
            "source": self.source,
        }

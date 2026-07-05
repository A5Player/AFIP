from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Candle:
    time: Optional[int]
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def is_valid(self) -> bool:
        return self.high >= self.low and self.high >= self.open and self.high >= self.close and self.low <= self.open and self.low <= self.close

    def range(self) -> float:
        return self.high - self.low

    def body(self) -> float:
        return abs(self.close - self.open)

    def direction(self) -> str:
        if self.close > self.open:
            return "BUY"
        if self.close < self.open:
            return "SELL"
        return "FLAT"

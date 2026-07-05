class SpreadNormalizer:
    def __init__(self, point_size: float = 0.01):
        self.point_size = point_size

    def from_bid_ask(self, bid: float, ask: float) -> float:
        if bid is None or ask is None:
            return 999.0
        if self.point_size <= 0:
            raise ValueError("point_size must be positive")
        return abs(ask - bid) / self.point_size

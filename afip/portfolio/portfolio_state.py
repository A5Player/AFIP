from dataclasses import dataclass

@dataclass
class PortfolioState:
    balance: float = 0.0
    equity: float = 0.0
    open_positions: int = 0
    floating_profit: float = 0.0

    def to_dict(self) -> dict:
        return {
            "balance": self.balance,
            "equity": self.equity,
            "open_positions": self.open_positions,
            "floating_profit": self.floating_profit,
        }

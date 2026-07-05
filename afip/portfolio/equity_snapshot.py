"""Portfolio equity snapshot model for production portfolio accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquitySnapshot:
    """Normalized portfolio equity state for one account."""

    status: str
    account_id: str
    balance: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    net_asset_value: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic dictionary for runtime and report layers."""
        return {
            "status": self.status,
            "account_id": self.account_id,
            "balance": self.balance,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "equity": self.equity,
            "net_asset_value": self.net_asset_value,
            "reason": self.reason,
        }

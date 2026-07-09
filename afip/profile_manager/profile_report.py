"""Profile Manager report objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .profile_models import TradingProfile


@dataclass(frozen=True)
class ProfileManagerReport:
    status: str
    reason: str
    profile_gate: str
    market_regime: str
    signal_context: str
    profile: TradingProfile
    assigned_account_id: str
    mt5_terminal_path: str
    server: str
    login_mask: str
    ready_sections: tuple[str, ...]
    review_items: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    @property
    def profile_architecture_valid(self) -> bool:
        return self.profile.as_dict()["profile_is_account"] is False and self.profile.as_dict()["profile_is_mt5"] is False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["profile"] = self.profile.as_dict()
        data["profile_architecture_valid"] = self.profile_architecture_valid
        data["unit_system"] = "1 Unit = 0.01 Lot"
        return data

    def as_text(self) -> str:
        return (
            "AFIP Profile Manager\n"
            f"Status: {self.status}\n"
            f"Gate: {self.profile_gate}\n"
            f"Reason: {self.reason}\n"
            f"Profile: {self.profile.profile_name}\n"
            f"Market Regime: {self.market_regime}\n"
            f"Signal Context: {self.signal_context}\n"
            f"Assigned Account: {self.assigned_account_id or '-'}\n"
            f"Maximum Units: {self.profile.maximum_units}\n"
            f"Order Lots: {', '.join(str(lot) for lot in self.profile.order_lots)}\n"
            f"Review Items: {', '.join(self.review_items) if self.review_items else '-'}\n"
            f"Trading Logic Changed: {self.trading_logic_changed}"
        )

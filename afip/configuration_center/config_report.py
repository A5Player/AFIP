"""Configuration Center report objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config_models import BrokerAccountConfig, CapitalConfiguration, DashboardConfiguration, RiskConfiguration, WalkForwardConfiguration


@dataclass(frozen=True)
class ConfigurationCenterReport:
    status: str
    reason: str
    configuration_gate: str
    market_regime: str
    signal_context: str
    accounts: tuple[BrokerAccountConfig, ...]
    risk: RiskConfiguration
    walk_forward: WalkForwardConfiguration
    dashboard: DashboardConfiguration
    capital: CapitalConfiguration
    ready_sections: tuple[str, ...]
    review_items: tuple[str, ...]
    trading_logic_changed: bool = False

    @property
    def enabled_accounts(self) -> int:
        return sum(1 for account in self.accounts if account.enabled)

    @property
    def all_sections_ready(self) -> bool:
        required = {"broker_accounts", "risk", "walk_forward", "dashboard", "capital"}
        return required.issubset(set(self.ready_sections)) and not self.review_items

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["accounts"] = [account.as_dict() for account in self.accounts]
        data["enabled_accounts"] = self.enabled_accounts
        data["all_sections_ready"] = self.all_sections_ready
        return data

    def as_text(self) -> str:
        return (
            "AFIP Configuration Center\n"
            f"Status: {self.status}\n"
            f"Gate: {self.configuration_gate}\n"
            f"Reason: {self.reason}\n"
            f"Market Regime: {self.market_regime}\n"
            f"Signal Context: {self.signal_context}\n"
            f"Enabled Accounts: {self.enabled_accounts}\n"
            f"Ready Sections: {', '.join(self.ready_sections)}\n"
            f"Review Items: {', '.join(self.review_items) if self.review_items else '-'}\n"
            f"Trading Logic Changed: {self.trading_logic_changed}"
        )

"""Configuration Center models for AFIP Command Center.

The module stores dashboard-facing configuration metadata only. It does not
open orders, modify strategy rules, or change runtime trading decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


def _clean(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _clean(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


@dataclass(frozen=True)
class BrokerAccountConfig:
    """Broker/account configuration shown in dashboard settings."""

    account_id: str
    broker: str
    account_name: str
    account_type: str
    server: str
    login_mask: str
    symbol: str
    enabled: bool
    status_icon: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "BrokerAccountConfig":
        broker = _upper(raw.get("broker", "XM"), "XM")
        account_type = _upper(raw.get("account_type", "DEMO"), "DEMO")
        enabled = _bool(raw.get("enabled", True), True)
        login = _clean(raw.get("login", raw.get("login_mask", "****")), "****")
        login_mask = login if "*" in login else f"****{login[-2:]}" if len(login) >= 2 else "****"
        return cls(
            account_id=_clean(raw.get("account_id", raw.get("id", "account_1")), "account_1"),
            broker=broker,
            account_name=_clean(raw.get("account_name", raw.get("name", f"{broker} {account_type}")), f"{broker} {account_type}"),
            account_type=account_type,
            server=_clean(raw.get("server", "XMGlobal-MT5 6"), "XMGlobal-MT5 6"),
            login_mask=login_mask,
            symbol=_upper(raw.get("symbol", "GOLD#"), "GOLD#"),
            enabled=enabled,
            status_icon="🟢" if enabled else "⚪",
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskConfiguration:
    lot_size: float
    max_positions: int
    max_daily_loss_percent: float
    max_drawdown_percent: float
    risk_mode: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RiskConfiguration":
        return cls(
            lot_size=max(0.0, _float(raw.get("lot_size", 0.01), 0.01)),
            max_positions=max(1, int(_float(raw.get("max_positions", 1), 1))),
            max_daily_loss_percent=max(0.0, _float(raw.get("max_daily_loss_percent", 2.0), 2.0)),
            max_drawdown_percent=max(0.0, _float(raw.get("max_drawdown_percent", 10.0), 10.0)),
            risk_mode=_upper(raw.get("risk_mode", "CONSERVATIVE"), "CONSERVATIVE"),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WalkForwardConfiguration:
    enabled: bool
    history_days: int
    learning_enabled: bool
    lookahead_protection: bool

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "WalkForwardConfiguration":
        return cls(
            enabled=_bool(raw.get("enabled", True), True),
            history_days=max(30, int(_float(raw.get("history_days", 365), 365))),
            learning_enabled=_bool(raw.get("learning_enabled", True), True),
            lookahead_protection=_bool(raw.get("lookahead_protection", True), True),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardConfiguration:
    language: str
    refresh_seconds: int
    theme: str
    show_top10: bool
    show_bilingual_names: bool

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "DashboardConfiguration":
        return cls(
            language=_clean(raw.get("language", "TH"), "TH").upper(),
            refresh_seconds=max(1, int(_float(raw.get("refresh_seconds", 5), 5))),
            theme=_upper(raw.get("theme", "DARK"), "DARK"),
            show_top10=_bool(raw.get("show_top10", True), True),
            show_bilingual_names=_bool(raw.get("show_bilingual_names", True), True),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapitalConfiguration:
    base_currency: str
    initial_capital: float
    deposits: float
    withdrawals: float
    monthly_target_percent: float

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CapitalConfiguration":
        return cls(
            base_currency=_upper(raw.get("base_currency", "USD"), "USD"),
            initial_capital=max(0.0, _float(raw.get("initial_capital", 100.0), 100.0)),
            deposits=max(0.0, _float(raw.get("deposits", 0.0), 0.0)),
            withdrawals=max(0.0, _float(raw.get("withdrawals", 0.0), 0.0)),
            monthly_target_percent=max(0.0, _float(raw.get("monthly_target_percent", 5.0), 5.0)),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

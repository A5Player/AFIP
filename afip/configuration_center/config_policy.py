"""Configuration readiness policy for AFIP Command Center."""

from __future__ import annotations

from typing import Any, Mapping

from .config_models import BrokerAccountConfig, CapitalConfiguration, DashboardConfiguration, RiskConfiguration, WalkForwardConfiguration
from .config_report import ConfigurationCenterReport

_SAFE_EXECUTION_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


def build_configuration_report(record: Mapping[str, Any]) -> ConfigurationCenterReport:
    market_regime = str(record.get("market_regime", "")).strip().upper()
    signal_context = str(record.get("signal_context", record.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
    execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()

    accounts_raw = record.get("accounts") or _default_accounts()
    accounts = tuple(BrokerAccountConfig.from_mapping(item) for item in accounts_raw)
    risk = RiskConfiguration.from_mapping(record.get("risk", {}))
    walk_forward = WalkForwardConfiguration.from_mapping(record.get("walk_forward", {}))
    dashboard = DashboardConfiguration.from_mapping(record.get("dashboard", {}))
    capital = CapitalConfiguration.from_mapping(record.get("capital", {}))

    ready_sections: list[str] = []
    review_items: list[str] = []

    if accounts and any(account.enabled for account in accounts):
        ready_sections.append("broker_accounts")
    else:
        review_items.append("enabled_broker_account_required")

    if risk.lot_size > 0 and risk.max_positions >= 1 and risk.max_drawdown_percent > 0:
        ready_sections.append("risk")
    else:
        review_items.append("risk_configuration_incomplete")

    if walk_forward.enabled and walk_forward.lookahead_protection:
        ready_sections.append("walk_forward")
    else:
        review_items.append("walk_forward_lookahead_protection_required")

    if dashboard.show_bilingual_names and dashboard.refresh_seconds >= 1:
        ready_sections.append("dashboard")
    else:
        review_items.append("dashboard_bilingual_settings_required")

    if capital.initial_capital > 0:
        ready_sections.append("capital")
    else:
        review_items.append("initial_capital_required")

    if not market_regime:
        return _report("BLOCKED", "market_regime_required", "BLOCKED", market_regime, signal_context, accounts, risk, walk_forward, dashboard, capital, ready_sections, review_items)
    if execution_mode not in _SAFE_EXECUTION_MODES:
        return _report("BLOCKED", "live_execution_not_allowed_for_configuration_center", "BLOCKED", market_regime, signal_context, accounts, risk, walk_forward, dashboard, capital, ready_sections, review_items)
    if review_items:
        return _report("REVIEW", "configuration_review_required", "REVIEW", market_regime, signal_context, accounts, risk, walk_forward, dashboard, capital, ready_sections, review_items)
    return _report("READY", "configuration_center_ready", "CONFIGURATION_CENTER_READY", market_regime, signal_context, accounts, risk, walk_forward, dashboard, capital, ready_sections, review_items)


def _report(
    status: str,
    reason: str,
    gate: str,
    market_regime: str,
    signal_context: str,
    accounts: tuple[BrokerAccountConfig, ...],
    risk: RiskConfiguration,
    walk_forward: WalkForwardConfiguration,
    dashboard: DashboardConfiguration,
    capital: CapitalConfiguration,
    ready_sections: list[str],
    review_items: list[str],
) -> ConfigurationCenterReport:
    return ConfigurationCenterReport(
        status=status,
        reason=reason,
        configuration_gate=gate,
        market_regime=market_regime,
        signal_context=signal_context,
        accounts=accounts,
        risk=risk,
        walk_forward=walk_forward,
        dashboard=dashboard,
        capital=capital,
        ready_sections=tuple(ready_sections),
        review_items=tuple(review_items),
    )


def _default_accounts() -> list[dict[str, Any]]:
    return [
        {"account_id": "xm_demo_100", "broker": "XM", "account_name": "XM Demo 100", "account_type": "DEMO", "server": "XMGlobal-MT5 6", "login": "100001", "symbol": "GOLD#", "enabled": True},
        {"account_id": "xm_demo_1000", "broker": "XM", "account_name": "XM Demo 1000", "account_type": "DEMO", "server": "XMGlobal-MT5 6", "login": "100002", "symbol": "GOLD#", "enabled": True},
    ]

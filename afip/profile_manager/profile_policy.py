"""Profile readiness policy for Milestone H Pack 3."""

from __future__ import annotations

from typing import Any, Mapping

from .profile_models import TradingProfile
from .profile_report import ProfileManagerReport

_SAFE_EXECUTION_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


def build_profile_report(record: Mapping[str, Any]) -> ProfileManagerReport:
    market_regime = str(record.get("market_regime", "")).strip().upper()
    signal_context = str(record.get("signal_context", record.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
    execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()
    profile = TradingProfile.from_mapping(record.get("profile", record))
    account = record.get("account", {}) or {}
    terminal = record.get("mt5", {}) or {}
    login = str(account.get("login", record.get("login", ""))).strip()
    login_mask = "****" if not login else f"****{login[-2:]}"
    ready_sections: list[str] = []
    review_items: list[str] = []

    if profile.broker == "XM" and profile.symbol == "GOLD#":
        ready_sections.append("broker_symbol_policy")
    else:
        review_items.append("version1_xm_gold_only_required")
    if profile.maximum_units >= 1 and profile.unit_lot_size == 0.01 and all(lot == 0.01 for lot in profile.order_lots):
        ready_sections.append("unit_system")
    else:
        review_items.append("unit_system_must_use_001_lot_per_unit")
    if profile.documentation and all(item.documentation.thai_description and item.documentation.english_description for item in profile.documentation):
        ready_sections.append("setting_documentation")
    else:
        review_items.append("setting_documentation_required")
    if profile.research_mode or profile.profile_type in {"CONSERVATIVE", "BALANCED", "GROWTH", "CUSTOM", "RESEARCH"}:
        ready_sections.append("profile_policy")
    else:
        review_items.append("known_profile_type_required")

    if not market_regime:
        return _report("BLOCKED", "market_regime_required", "BLOCKED", market_regime, signal_context, profile, account, terminal, login_mask, ready_sections, review_items)
    if execution_mode not in _SAFE_EXECUTION_MODES:
        return _report("BLOCKED", "live_execution_not_allowed_for_profile_manager", "BLOCKED", market_regime, signal_context, profile, account, terminal, login_mask, ready_sections, review_items)
    if review_items:
        return _report("REVIEW", "profile_review_required", "REVIEW", market_regime, signal_context, profile, account, terminal, login_mask, ready_sections, review_items)
    return _report("READY", "profile_manager_ready", "PROFILE_MANAGER_READY", market_regime, signal_context, profile, account, terminal, login_mask, ready_sections, review_items)


def _report(status: str, reason: str, gate: str, market_regime: str, signal_context: str, profile: TradingProfile, account: Mapping[str, Any], terminal: Mapping[str, Any], login_mask: str, ready_sections: list[str], review_items: list[str]) -> ProfileManagerReport:
    return ProfileManagerReport(
        status=status,
        reason=reason,
        profile_gate=gate,
        market_regime=market_regime,
        signal_context=signal_context,
        profile=profile,
        assigned_account_id=str(account.get("account_id", account.get("id", ""))).strip(),
        mt5_terminal_path=str(terminal.get("path", "")).strip(),
        server=str(account.get("server", "XMGlobal-MT5 6")).strip(),
        login_mask=login_mask,
        ready_sections=tuple(ready_sections),
        review_items=tuple(review_items),
    )

"""MT5 live account read-only runtime for Production Bring-up Pack 2."""

from __future__ import annotations

from typing import Any, Mapping

from afip.broker.mt5_adapter import MT5Adapter

from .models import MT5LiveAccountReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"


def _text(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _mask_login(value: Any) -> str:
    raw = _text(value, "configured")
    if raw in {"UNKNOWN", "configured", "account_info_unavailable"}:
        return raw
    if len(raw) <= 4:
        return "*" * len(raw)
    return "*" * max(0, len(raw) - 4) + raw[-4:]


class MT5LiveAccountRuntime:
    """Read MT5 account telemetry without changing trading logic."""

    def evaluate_one(self, record: Mapping[str, Any] | None = None) -> MT5LiveAccountReport:
        record = record or {}
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        live = bool(record.get("live_execution_enabled", False)) or _upper(record.get("mode", ""), "") == "LIVE"
        if live:
            return self._blocked(broker, symbol, "live_execution_blocked_for_mt5_live_account")
        if broker != VERSION1_BROKER:
            return self._blocked(broker, symbol, "version1_xm_only_required_for_mt5_live_account")
        if symbol != VERSION1_SYMBOL:
            return self._blocked(broker, symbol, "version1_gold_only_required_for_mt5_live_account")

        account, tick, symbol_info = self._read_sources(record, symbol)
        account_available = bool(account.get("available", False))
        tick_available = bool(tick.get("available", False))
        point = _float(symbol_info.get("point", record.get("point", 0.01)), 0.01)
        bid = _float(tick.get("bid", record.get("bid", 0.0)), 0.0)
        ask = _float(tick.get("ask", record.get("ask", 0.0)), 0.0)
        spread = _float(record.get("spread_points"), 0.0)
        if spread <= 0 and point > 0 and ask > 0 and bid > 0:
            spread = round((ask - bid) / point, 2)
        status = "READY"
        reason = "mt5_live_account_ready"
        gate = "MT5_LIVE_ACCOUNT_READY"
        if not account_available:
            status = "WAITING"
            reason = account.get("reason", "mt5_account_info_waiting")
            gate = "MT5_ACCOUNT_WAITING"
        elif not tick_available:
            status = "WAITING"
            reason = tick.get("reason", "mt5_tick_waiting")
            gate = "MT5_TICK_WAITING"
        elif spread >= _float(record.get("spread_review_limit", 35.0), 35.0):
            status = "REVIEW"
            reason = "mt5_spread_review_required"
            gate = "MT5_SPREAD_REVIEW"

        return MT5LiveAccountReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            server=_text(account.get("server", record.get("server", "UNKNOWN")), "UNKNOWN"),
            login=_mask_login(account.get("login", record.get("login", "configured"))),
            account_name=_text(account.get("name", record.get("account_name", "MT5 Account")), "MT5 Account"),
            balance=round(_float(account.get("balance", record.get("balance", 0.0)), 0.0), 2),
            equity=round(_float(account.get("equity", record.get("equity", 0.0)), 0.0), 2),
            margin=round(_float(account.get("margin", record.get("margin", 0.0)), 0.0), 2),
            free_margin=round(_float(account.get("free_margin", account.get("margin_free", record.get("free_margin", 0.0))), 0.0), 2),
            leverage=_text(account.get("leverage", record.get("leverage", "UNKNOWN")), "UNKNOWN"),
            currency=_text(account.get("currency", record.get("currency", "UNKNOWN")), "UNKNOWN"),
            tick_available=tick_available,
            bid=bid,
            ask=ask,
            spread_points=spread,
            point=point,
            digits=_text(symbol_info.get("digits", record.get("digits", "UNKNOWN")), "UNKNOWN"),
            last_tick_time=_text(tick.get("time", record.get("last_tick_time", "UNKNOWN")), "UNKNOWN"),
            account_gate=gate,
            dashboard_message_th="แสดงบัญชี MT5 แบบอ่านอย่างเดียวโดยไม่เปิดการส่งคำสั่งเงินจริง",
            dashboard_message_en="Displays read-only MT5 account telemetry without enabling live order execution.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any] | None = None) -> MT5LiveAccountReport:
        return self.evaluate_one(record)

    def _read_sources(self, record: Mapping[str, Any], symbol: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        account = dict(record.get("mt5_account_info", {}) or {})
        tick = dict(record.get("mt5_tick", {}) or {})
        symbol_info = dict(record.get("mt5_symbol_info", {}) or {})
        if account or tick or symbol_info:
            account.setdefault("available", bool(account))
            tick.setdefault("available", bool(tick))
            symbol_info.setdefault("available", bool(symbol_info))
            return account, tick, symbol_info
        if not bool(record.get("mt5_live_account_enabled", False)):
            return ({"available": False, "reason": "mt5_live_account_not_requested"}, {"available": False, "reason": "mt5_live_tick_not_requested"}, {"available": False, "reason": "mt5_symbol_info_not_requested"})
        adapter = MT5Adapter.from_installed_package(enabled=True)
        initialize = adapter.initialize()
        if not initialize.get("initialized", False):
            reason = initialize.get("reason", "mt5_initialize_failed")
            adapter.shutdown()
            return ({"available": False, "reason": reason}, {"available": False, "reason": reason}, {"available": False, "reason": reason})
        try:
            adapter.symbol_select(symbol)
            return adapter.account_info(), adapter.latest_tick(symbol), adapter.symbol_info(symbol)
        finally:
            adapter.shutdown()

    def _blocked(self, broker: str, symbol: str, reason: str) -> MT5LiveAccountReport:
        return MT5LiveAccountReport(
            status="BLOCKED",
            reason=reason,
            broker=broker,
            symbol=symbol,
            server="BLOCKED",
            login="BLOCKED",
            account_name="BLOCKED",
            balance=0.0,
            equity=0.0,
            margin=0.0,
            free_margin=0.0,
            leverage="BLOCKED",
            currency="BLOCKED",
            tick_available=False,
            bid=0.0,
            ask=0.0,
            spread_points=0.0,
            point=0.0,
            digits="BLOCKED",
            last_tick_time="BLOCKED",
            account_gate="LIVE_EXECUTION_BLOCKED" if "live" in reason else "VERSION1_POLICY_BLOCKED",
            dashboard_message_th="บล็อกการอ่านบัญชีตามนโยบายความปลอดภัย Version 1",
            dashboard_message_en="Blocks account telemetry according to Version 1 safety policy.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )

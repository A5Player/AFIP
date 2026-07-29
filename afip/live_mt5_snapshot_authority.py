"""Read-only live MT5 snapshot publisher for AFIP Pro.

Uses an MT5 session already owned by the profile execution worker. It never
initializes, logs in, reconnects, launches a terminal, checks/sends orders, or
changes execution authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _masked_login(value: Any) -> str:
    text = str(value or "")
    return "NOT_CONFIGURED" if not text else f"****{text[-4:]}"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


def publish_live_mt5_snapshot(
    *,
    profile: Any,
    mt5: Any,
    account: Any,
    value_getter: Callable[[Any, str, Any], Any] | None = None,
) -> dict[str, Any]:
    """Publish account, tick and position telemetry from an existing session."""
    get = value_getter or _value
    checked_at = datetime.now(timezone.utc).isoformat()
    symbol = str(get(profile, "symbol", "GOLD#"))
    runtime_directory = Path(get(profile, "runtime_directory", "runtime"))

    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    terminal = mt5.terminal_info()
    positions = tuple(mt5.positions_get(symbol=symbol) or ())
    orders_get = getattr(mt5, "orders_get", None)
    orders = tuple(orders_get(symbol=symbol) or ()) if callable(orders_get) else ()

    point = get(symbol_info, "point")
    bid = get(tick, "bid")
    ask = get(tick, "ask")
    spread_points = None
    try:
        if point and bid is not None and ask is not None:
            spread_points = round((float(ask) - float(bid)) / float(point), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        spread_points = None

    actual_login = get(account, "login", get(profile, "login", ""))
    actual_server = get(account, "server", get(profile, "server", "DATA_UNAVAILABLE"))
    connected = bool(get(terminal, "connected", True))
    position_rows: list[dict[str, Any]] = []
    for position in positions:
        position_rows.append({
            "ticket": get(position, "ticket"),
            "identifier": get(position, "identifier"),
            "symbol": get(position, "symbol", symbol),
            "type": "BUY" if get(position, "type") == 0 else "SELL" if get(position, "type") == 1 else str(get(position, "type", "UNKNOWN")),
            "type_code": get(position, "type"),
            "side": "BUY" if get(position, "type") == 0 else "SELL" if get(position, "type") == 1 else "UNKNOWN",
            "volume": get(position, "volume"),
            "entry_price": get(position, "price_open"),
            "current_price": get(position, "price_current"),
            "stop_loss": get(position, "sl"),
            "take_profit": get(position, "tp"),
            "sl": get(position, "sl"),
            "tp": get(position, "tp"),
            "price_open": get(position, "price_open"),
            "price_current": get(position, "price_current"),
            "profit": get(position, "profit"),
            "swap": get(position, "swap"),
            "magic": get(position, "magic"),
            "comment": get(position, "comment"),
            "opened_at_epoch": get(position, "time"),
            "opened_at_msc": get(position, "time_msc"),
        })
    position_tickets = [row["ticket"] for row in position_rows if row.get("ticket") not in (None, "")]

    payload: dict[str, Any] = {
        "schema_version": "AFIP_PRO_LIVE_MT5_SNAPSHOT_V1",
        "producer": "DemoExecutionGatewayExistingSession",
        "profile_id": str(get(profile, "profile_id", "UNKNOWN")),
        "enabled": bool(get(profile, "enabled", True)),
        "connection_status": "CONNECTED" if connected else "DEGRADED",
        "terminal_exists": True,
        "initialized": True,
        "authenticated": account is not None,
        "account_match": str(actual_login) == str(get(profile, "login", actual_login)),
        "server_match": str(actual_server).casefold() == str(get(profile, "server", actual_server)).casefold(),
        "symbol_available": symbol_info is not None,
        "tick_available": tick is not None,
        "latency_ms": None,
        "reconnect_attempts": 0,
        "account": _masked_login(actual_login),
        "server": str(actual_server),
        "terminal_path": str(get(profile, "mt5_terminal", "DATA_UNAVAILABLE")),
        "reason": "live_telemetry_from_existing_profile_runtime_session",
        "checked_at_utc": checked_at,
        "snapshot_checked_at_utc": checked_at,
        "snapshot_age_seconds": 0,
        "currency": str(get(account, "currency", "DATA_UNAVAILABLE")),
        "balance": get(account, "balance"),
        "equity": get(account, "equity"),
        "margin": get(account, "margin"),
        "free_margin": get(account, "margin_free"),
        "floating_profit": get(account, "profit"),
        "margin_free": get(account, "margin_free"),
        "profit": get(account, "profit"),
        "trade_allowed": get(account, "trade_allowed"),
        "positions_total": len(positions),
        "orders_total": len(orders),
        "positions": position_rows,
        "position_tickets": position_tickets,
        "current_tickets": position_tickets,
        "bid": bid,
        "ask": ask,
        "spread_points": spread_points,
        "digits": get(symbol_info, "digits"),
        "point_size": point,
        "symbol": symbol,
        "monitoring_mode": "EXISTING_RUNTIME_SESSION_READ_ONLY",
        "process_alive": True,
        "evidence_kind": "LIVE",
        "execution_authority": False,
        "order_check_called": False,
        "order_send_called": False,
        "verified_snapshot": bool(connected and account is not None and symbol_info is not None and tick is not None),
    }
    _atomic_json(runtime_directory / "mt5_live_snapshot.json", payload)
    return payload

"""
AFIP MT5 read-only adapter.

Safety policy:
- Market/account data only.
- No order_send wrapper.
- MT5 connection is opt-in.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


class MT5Adapter:
    """
    Read-only MT5 adapter for Production Sprint 3.

    The adapter accepts an injected mt5_client for tests and production wiring.
    It never imports MetaTrader5 at module import time, so AFIP remains runnable
    on machines without the MT5 Python package.
    """

    TIMEFRAME_MAP = {
        "M1": "TIMEFRAME_M1",
        "M5": "TIMEFRAME_M5",
        "M15": "TIMEFRAME_M15",
        "H1": "TIMEFRAME_H1",
        "H4": "TIMEFRAME_H4",
        "D1": "TIMEFRAME_D1",
    }

    def __init__(self, mt5_client: Any | None = None, enabled: bool = False):
        self.mt5_client = mt5_client
        self.enabled = enabled
        self.initialized = False

    @classmethod
    def from_installed_package(cls, enabled: bool = True) -> "MT5Adapter":
        if not enabled:
            return cls(mt5_client=None, enabled=False)
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception:
            return cls(mt5_client=None, enabled=False)
        return cls(mt5_client=mt5, enabled=True)

    def is_available(self) -> bool:
        return self.enabled and self.mt5_client is not None

    def initialize(self) -> dict:
        if not self.is_available():
            return {"available": False, "initialized": False, "reason": "mt5_adapter_disabled_or_package_missing"}

        initialize = getattr(self.mt5_client, "initialize", None)
        if initialize is None:
            self.initialized = True
            return {"available": True, "initialized": True, "reason": "initialize_not_required"}

        ok = bool(initialize())
        self.initialized = ok
        return {"available": True, "initialized": ok, "reason": "initialized" if ok else "initialize_failed"}

    def shutdown(self) -> None:
        shutdown = getattr(self.mt5_client, "shutdown", None)
        if self.is_available() and shutdown is not None:
            shutdown()
        self.initialized = False

    def symbol_select(self, symbol: str = "XAUUSD") -> dict:
        if not self.is_available():
            return {"symbol": symbol, "selected": False, "reason": "mt5_adapter_disabled"}

        selector = getattr(self.mt5_client, "symbol_select", None)
        if selector is None:
            return {"symbol": symbol, "selected": True, "reason": "symbol_select_not_required"}

        selected = bool(selector(symbol, True))
        return {"symbol": symbol, "selected": selected, "reason": "selected" if selected else "symbol_select_failed"}

    def latest_tick(self, symbol: str = "XAUUSD") -> dict:
        if not self.is_available():
            return {"symbol": symbol, "available": False, "reason": "mt5_adapter_disabled"}

        tick_reader = getattr(self.mt5_client, "symbol_info_tick", None)
        if tick_reader is None:
            return {"symbol": symbol, "available": False, "reason": "tick_reader_missing"}

        tick = tick_reader(symbol)
        if tick is None:
            return {"symbol": symbol, "available": False, "reason": "tick_unavailable"}

        return {
            "symbol": symbol,
            "available": True,
            "bid": getattr(tick, "bid", None),
            "ask": getattr(tick, "ask", None),
            "last": getattr(tick, "last", None),
            "time": getattr(tick, "time", None),
        }

    def symbol_info(self, symbol: str = "XAUUSD") -> dict:
        if not self.is_available():
            return {"symbol": symbol, "available": False, "reason": "mt5_adapter_disabled"}

        info_reader = getattr(self.mt5_client, "symbol_info", None)
        info = info_reader(symbol) if info_reader is not None else None
        if info is None:
            return {"symbol": symbol, "available": False, "reason": "symbol_info_unavailable"}

        data = self._to_dict(info)
        return {
            "symbol": symbol,
            "available": True,
            "digits": data.get("digits"),
            "point": data.get("point"),
            "trade_contract_size": data.get("trade_contract_size"),
            "raw": data,
        }

    def account_info(self) -> dict:
        if not self.is_available():
            return {"available": False, "reason": "mt5_adapter_disabled"}

        account_reader = getattr(self.mt5_client, "account_info", None)
        account = account_reader() if account_reader is not None else None
        if account is None:
            return {"available": False, "reason": "account_info_unavailable"}

        data = self._to_dict(account)
        return {
            "available": True,
            "login": data.get("login"),
            "server": data.get("server"),
            "balance": data.get("balance"),
            "equity": data.get("equity"),
            "margin": data.get("margin"),
            "free_margin": data.get("margin_free", data.get("free_margin")),
            "currency": data.get("currency"),
            "raw": data,
        }

    def copy_rates(self, symbol: str, timeframe: str, count: int = 100) -> dict:
        if not self.is_available():
            return {"symbol": symbol, "timeframe": timeframe, "available": False, "reason": "mt5_adapter_disabled", "rates": []}

        rates_reader = getattr(self.mt5_client, "copy_rates_from_pos", None)
        if rates_reader is None:
            return {"symbol": symbol, "timeframe": timeframe, "available": False, "reason": "rates_reader_missing", "rates": []}

        mt5_timeframe = self._resolve_timeframe(timeframe)
        if mt5_timeframe is None:
            return {"symbol": symbol, "timeframe": timeframe, "available": False, "reason": "unsupported_timeframe", "rates": []}

        rows = rates_reader(symbol, mt5_timeframe, 0, count)
        if rows is None:
            return {"symbol": symbol, "timeframe": timeframe, "available": False, "reason": "rates_unavailable", "rates": []}

        rates = [self._to_dict(row) for row in list(rows)]
        return {"symbol": symbol, "timeframe": timeframe, "available": True, "reason": "rates_available", "rates": rates}

    def _resolve_timeframe(self, timeframe: str) -> Any | None:
        attr_name = self.TIMEFRAME_MAP.get(timeframe.upper())
        if attr_name is None:
            return None
        return getattr(self.mt5_client, attr_name, attr_name)

    @staticmethod
    def _to_dict(value: Any) -> dict:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        if is_dataclass(value):
            return asdict(value)
        if hasattr(value, "_asdict"):
            return dict(value._asdict())
        if hasattr(value, "dtype") and hasattr(value, "tolist"):
            # numpy scalar/record fallback
            try:
                names = value.dtype.names or []
                return {name: value[name].item() if hasattr(value[name], "item") else value[name] for name in names}
            except Exception:
                pass
        return {key: getattr(value, key) for key in dir(value) if not key.startswith("_") and not callable(getattr(value, key))}

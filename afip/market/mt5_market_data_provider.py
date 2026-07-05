"""
AFIP MT5 market data provider.

Read-only integration that turns live MT5 tick/OHLC data into AFIP snapshots.
Falls back to simulation when MT5 is disabled, missing, or incomplete.
"""

from __future__ import annotations

from afip.broker.mt5_adapter import MT5Adapter
from afip.market.candle_snapshot_builder import CandleSnapshotBuilder
from afip.market.simulation_market_data_provider import SimulationMarketDataProvider
from afip.symbol.mt5_symbol_resolver import MT5SymbolResolver


class MT5MarketDataProvider:
    DEFAULT_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
    DEFAULT_GOLD_POINT_SIZE = 0.01

    def __init__(self, adapter=None, fallback_provider=None, snapshot_builder=None):
        self.adapter = adapter or MT5Adapter(enabled=False)
        self.fallback_provider = fallback_provider or SimulationMarketDataProvider()
        self.snapshot_builder = snapshot_builder or CandleSnapshotBuilder()

    @classmethod
    def from_installed_package(cls, enabled: bool = True):
        return cls(adapter=MT5Adapter.from_installed_package(enabled=enabled))

    def connection_check(self, symbol: str = "GOLD#") -> dict:
        init = self.adapter.initialize()
        resolution = MT5SymbolResolver(self.adapter, preferred_symbol="GOLD#").resolve(symbol) if init.get("initialized") else {
            "requested": symbol,
            "resolved": symbol,
            "selected": False,
            "reason": init.get("reason"),
            "candidates": [symbol, "GOLD#", "GOLD", "XAUUSD#", "XAUUSD"],
        }
        resolved_symbol = resolution.get("resolved", symbol)
        symbol_select = {
            "symbol": resolved_symbol,
            "selected": bool(resolution.get("selected")),
            "reason": resolution.get("reason"),
            "requested": resolution.get("requested", symbol),
            "candidates": resolution.get("candidates", []),
        }
        tick = self.adapter.latest_tick(resolved_symbol) if symbol_select.get("selected") else {"symbol": resolved_symbol, "available": False, "reason": symbol_select.get("reason")}
        symbol_info = self.adapter.symbol_info(resolved_symbol) if symbol_select.get("selected") else {"symbol": resolved_symbol, "available": False, "reason": symbol_select.get("reason")}
        account_info = self.adapter.account_info() if init.get("initialized") else {"available": False, "reason": init.get("reason")}
        point_size = self._point_size(symbol_info)
        spread = self._spread_points(tick.get("bid"), tick.get("ask"), point_size=point_size) if tick.get("available") else 999

        ready = bool(init.get("initialized") and symbol_select.get("selected") and tick.get("available"))
        return {
            "status": "READY" if ready else "FALLBACK_READY",
            "symbol": resolved_symbol,
            "requested_symbol": symbol,
            "symbol_resolution": resolution,
            "execution": "LOCKED_SIMULATION_ONLY",
            "initialize": init,
            "symbol_select": symbol_select,
            "tick": tick,
            "symbol_info": symbol_info,
            "point_size": point_size,
            "spread": spread,
            "account_info": account_info,
        }

    def latest_snapshot(self, symbol: str = "GOLD#") -> dict:
        tick = self.adapter.latest_tick(symbol)

        if not tick.get("available"):
            snapshot = self.fallback_provider.latest_snapshot(symbol)
            snapshot["source"] = "SIMULATION_FALLBACK"
            snapshot["fallback_reason"] = tick.get("reason")
            return snapshot

        symbol_info = self.adapter.symbol_info(symbol)
        point_size = self._point_size(symbol_info)
        bid = tick.get("bid")
        ask = tick.get("ask")
        spread = self._spread_points(bid=bid, ask=ask, point_size=point_size)
        price = bid or ask or tick.get("last") or 0
        return {
            "symbol": symbol,
            "closes": [price, price, price, price, price],
            "highs": [price, price, price, price, price],
            "lows": [price, price, price, price, price],
            "opens": [price, price, price, price, price],
            "volumes": [0, 0, 0, 0, 0],
            "spread": spread,
            "point_size": point_size,
            "source": "MT5_TICK",
            "tick": tick,
            "symbol_info": symbol_info,
        }

    def timeframe_snapshots(self, symbol: str = "GOLD#", timeframes=None, count: int = 100) -> dict:
        requested = tuple(timeframes or self.DEFAULT_TIMEFRAMES)
        snapshots = {}
        fallback_reasons = {}
        tick = self.adapter.latest_tick(symbol)
        symbol_info = self.adapter.symbol_info(symbol) if tick.get("available") else {}
        point_size = self._point_size(symbol_info)
        spread = self._spread_points(tick.get("bid"), tick.get("ask"), point_size=point_size) if tick.get("available") else 18

        for timeframe in requested:
            rates_result = self.adapter.copy_rates(symbol=symbol, timeframe=timeframe, count=count)
            if not rates_result.get("available") or not rates_result.get("rates"):
                snapshots[timeframe] = self.fallback_provider.latest_snapshot(symbol)
                snapshots[timeframe]["source"] = f"SIMULATION_FALLBACK_{timeframe}"
                snapshots[timeframe]["spread"] = spread
                snapshots[timeframe]["point_size"] = point_size
                fallback_reasons[timeframe] = rates_result.get("reason")
                continue

            snapshots[timeframe] = self.snapshot_builder.build(
                symbol=symbol,
                candles=rates_result["rates"],
                spread=spread,
                source=f"MT5_OHLC_{timeframe}",
            )
            snapshots[timeframe]["point_size"] = point_size
            snapshots[timeframe]["tick"] = tick

        return {
            "symbol": symbol,
            "source": "MT5_OHLC" if not fallback_reasons else "MIXED_MT5_SIMULATION_FALLBACK",
            "timeframes": snapshots,
            "fallback_reasons": fallback_reasons,
            "spread": spread,
            "point_size": point_size,
            "execution": "LOCKED_SIMULATION_ONLY",
        }

    @classmethod
    def _point_size(cls, symbol_info: dict | None) -> float:
        symbol_info = symbol_info or {}
        raw = symbol_info.get("raw", {}) if isinstance(symbol_info, dict) else {}
        candidates = (symbol_info.get("point"), raw.get("point"), cls.DEFAULT_GOLD_POINT_SIZE)
        for value in candidates:
            try:
                point_size = float(value)
            except (TypeError, ValueError):
                continue
            if point_size > 0:
                return point_size
        return cls.DEFAULT_GOLD_POINT_SIZE

    @staticmethod
    def _spread_points(bid, ask, point_size: float = DEFAULT_GOLD_POINT_SIZE) -> float:
        if bid is None or ask is None:
            return 999
        if point_size <= 0:
            point_size = MT5MarketDataProvider.DEFAULT_GOLD_POINT_SIZE
        return round(abs(float(ask) - float(bid)) / point_size, 2)

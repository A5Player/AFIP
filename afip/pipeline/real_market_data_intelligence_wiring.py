"""
AFIP — Real Market Data Intelligence integration.

Connects read-only MT5 OHLC snapshots to Multi-Timeframe Confluence
Intelligence and then to the official Modular Intelligence pipeline.
Execution remains locked to simulation only.
"""

from __future__ import annotations

from afip.market.mt5_market_data_provider import MT5MarketDataProvider
from afip.pipeline.modular_intelligence_pipeline import ModularIntelligencePipeline
from afip.pipeline.multi_timeframe_confluence_intelligence import MultiTimeframeConfluenceIntelligence
from afip.intelligence.trading_cost_intelligence import TradingCostIntelligence


class RealMarketDataIntelligenceWiring:
    """
    Integrate GOLD# real market data into AFIP Intelligence.

    Safety:
    - Reads tick/OHLC/account metadata only.
    - Does not execute orders.
    - Falls back to simulation snapshots if MT5 data is not available.
    """

    def __init__(self, market_data_provider=None, intelligence_pipeline=None, confluence_intelligence=None, trading_cost_intelligence=None):
        self.market_data_provider = market_data_provider or MT5MarketDataProvider.from_installed_package(enabled=True)
        self.intelligence_pipeline = intelligence_pipeline or ModularIntelligencePipeline()
        self.confluence_intelligence = confluence_intelligence or MultiTimeframeConfluenceIntelligence()
        self.trading_cost_intelligence = trading_cost_intelligence or TradingCostIntelligence()

    def run(self, symbol: str = "GOLD#", count: int = 100) -> dict:
        if hasattr(self.market_data_provider, "connection_check"):
            connection = self.market_data_provider.connection_check(symbol=symbol)
        else:
            connection = {
                "status": "READY",
                "symbol": symbol,
                "requested": symbol,
                "execution": "LOCKED_SIMULATION_ONLY",
                "init": "provider_compatibility_mode",
                "select": "provider_connection_check_unavailable",
                "tick": "provider_connection_check_unavailable",
            }
        resolved_symbol = connection.get("symbol", symbol)

        if hasattr(self.market_data_provider, "timeframe_snapshots"):
            timeframe_bundle = self.market_data_provider.timeframe_snapshots(
                symbol=resolved_symbol,
                count=count,
            )
        else:
            primary_snapshot = None
            if hasattr(self.market_data_provider, "snapshot"):
                try:
                    primary_snapshot = self.market_data_provider.snapshot(
                        symbol=resolved_symbol,
                        timeframe="H1",
                        count=count,
                    )
                except TypeError:
                    primary_snapshot = self.market_data_provider.snapshot(resolved_symbol)
            elif hasattr(self.market_data_provider, "get_snapshot"):
                try:
                    primary_snapshot = self.market_data_provider.get_snapshot(
                        symbol=resolved_symbol,
                        timeframe="H1",
                        count=count,
                    )
                except TypeError:
                    primary_snapshot = self.market_data_provider.get_snapshot(resolved_symbol)

            if primary_snapshot is None:
                primary_snapshot = {
                    "symbol": resolved_symbol,
                    "timeframe": "H1",
                    "source": "PROVIDER_COMPATIBILITY_FALLBACK",
                    "closes": [2300.0, 2300.5, 2301.0, 2301.5, 2302.0],
                    "highs": [2300.5, 2301.0, 2301.5, 2302.0, 2302.5],
                    "lows": [2299.5, 2300.0, 2300.5, 2301.0, 2301.5],
                    "spread": 30.0,
                }

            timeframe_bundle = {
                "status": "READY",
                "symbol": resolved_symbol,
                "requested": symbol,
                "execution": "LOCKED_SIMULATION_ONLY",
                "primary_timeframe": "H1",
                "source": "provider_snapshot_compatibility_mode",
                "timeframes": {
                    "H1": primary_snapshot,
                },
                "snapshots": {
                    "H1": primary_snapshot,
                },
            }
        snapshots = timeframe_bundle.get("timeframes", {})
        confluence = self.confluence_intelligence.build(snapshots)
        primary_timeframe = confluence.get("primary_timeframe")
        primary_snapshot = confluence.get("snapshot") or self.market_data_provider.latest_snapshot(resolved_symbol)

        trading_cost_intelligence = self.trading_cost_intelligence.assess(primary_snapshot, connection=connection)

        modular = self.intelligence_pipeline.run(primary_snapshot)
        modular["mode"] = "REAL_MARKET_DATA" if self._is_real_source(primary_snapshot) else "SIMULATION_FALLBACK"
        modular["data_source"] = primary_snapshot.get("source", "UNKNOWN")
        modular["primary_timeframe"] = primary_timeframe or "TICK"
        modular["confluence"] = confluence
        modular["trading_cost_intelligence"] = trading_cost_intelligence

        return {
            "status": "READY" if self._is_real_source(primary_snapshot) else "FALLBACK_READY",
            "symbol": resolved_symbol,
            "requested_symbol": symbol,
            "execution": "LOCKED_SIMULATION_ONLY",
            "connection": connection,
            "market_data": timeframe_bundle,
            "primary_timeframe": primary_timeframe or "TICK",
            "primary_snapshot": primary_snapshot,
            "multi_timeframe_confluence": confluence,
            "trading_cost_intelligence": trading_cost_intelligence,
            "modular_intelligence": modular,
        }

    @staticmethod
    def _is_real_source(snapshot: dict) -> bool:
        source = str(snapshot.get("source", ""))
        return source.startswith("MT5_OHLC") or source.startswith("MTF_CONFLUENCE_MT5_OHLC") or source == "MT5_TICK"

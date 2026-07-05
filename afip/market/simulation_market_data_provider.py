from afip.models.market_snapshot import MarketSnapshot

class SimulationMarketDataProvider:
    def latest_snapshot(self, symbol: str = "XAUUSD") -> dict:
        return MarketSnapshot(
            symbol=symbol,
            closes=[2300.0, 2300.4, 2301.1, 2302.0, 2303.2],
            highs=[2300.6, 2301.0, 2301.7, 2302.8, 2303.8],
            lows=[2299.5, 2300.0, 2300.7, 2301.3, 2302.6],
            spread=18,
            source="SIMULATION",
        ).to_dict()

    def stressed_snapshot(self, symbol: str = "XAUUSD") -> dict:
        return MarketSnapshot(
            symbol=symbol,
            closes=[2300.0, 2300.5, 2301.0, 2301.6, 2302.0],
            highs=[2300.7, 2301.2, 2302.0, 2302.8, 2303.5],
            lows=[2298.5, 2298.9, 2299.2, 2299.7, 2300.1],
            spread=75,
            source="SIMULATION_STRESS",
        ).to_dict()

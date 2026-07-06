"""Production Milestone C Pack 4 market factor runtime wrapper."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from afip.macro.macro_market_factor_runtime import MacroMarketFactorRuntime
from afip.macro.market_factor_cache import MarketFactorCache
from afip.macro.market_factor_provider import MarketFactorProvider, StaticMarketFactorProvider
from afip.research.market_signature import MarketSignatureEngine


class ProductionMilestoneCMarketFactorRuntime:
    """Run live-ready macro market factor scoring with compact market signature output."""

    def __init__(self, provider: MarketFactorProvider | None = None, cache: MarketFactorCache | None = None) -> None:
        self.provider = provider or StaticMarketFactorProvider({})
        self.runtime = MacroMarketFactorRuntime(provider=self.provider, cache=cache)
        self.signature_engine = MarketSignatureEngine()

    def run(self, current_time: datetime | None = None, raw_factors: Mapping[str, object] | None = None) -> dict[str, object]:
        state = self.runtime.run(current_time=current_time, raw_factors=raw_factors)
        bias = state.gold_market_bias
        signature = self.signature_engine.build(
            {
                "dxy": state.dxy.get("direction"),
                "treasury_yield": state.treasury_yield.get("direction"),
                "real_yield": state.real_yield.get("direction"),
                "gold_market_bias": bias.get("bias"),
                "dxy_change_percent": state.raw_factors.get("dxy_change_percent", 0.0),
                "real_yield_change_bps": state.raw_factors.get("real_yield_change_bps", 0.0),
            }
        )
        result = state.as_dict()
        result["market_signature"] = signature.as_dict()
        result["package"] = "Production Milestone C Pack 4"
        return result

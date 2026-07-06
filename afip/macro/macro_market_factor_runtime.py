"""Live-ready macro market factor runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping

from .dxy_runtime import DxyRuntime
from .gold_market_bias_engine import GoldMarketBiasEngine
from .market_factor_cache import MarketFactorCache
from .market_factor_provider import EmptyMarketFactorProvider, MarketFactorProvider
from .real_yield_runtime import RealYieldRuntime
from .treasury_yield_runtime import TreasuryYieldRuntime


@dataclass(frozen=True)
class MacroMarketFactorState:
    """Complete macro market factor runtime state."""

    status: str
    source: str
    observed_at: str
    dxy: Mapping[str, object]
    treasury_yield: Mapping[str, object]
    real_yield: Mapping[str, object]
    gold_market_bias: Mapping[str, object]
    raw_factors: Mapping[str, float]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class MacroMarketFactorRuntime:
    """Build a gold macro factor state from provider data, cache, and factor assessments."""

    def __init__(self, provider: MarketFactorProvider | None = None, cache: MarketFactorCache | None = None) -> None:
        self.provider = provider or EmptyMarketFactorProvider()
        self.cache = cache or MarketFactorCache(ttl_seconds=300)
        self.dxy_runtime = DxyRuntime()
        self.treasury_runtime = TreasuryYieldRuntime()
        self.real_yield_runtime = RealYieldRuntime()
        self.bias_engine = GoldMarketBiasEngine()

    def run(self, current_time: datetime | None = None, raw_factors: Mapping[str, object] | None = None) -> MacroMarketFactorState:
        current_time = current_time or datetime.now(timezone.utc)
        if raw_factors is not None:
            factors = {str(key): self._to_float(value) for key, value in raw_factors.items()}
            source = "DIRECT_MARKET_FACTOR_INPUT"
            observed_at = current_time
            provider_reason = "direct_market_factor_input"
        else:
            cached = self.cache.get(current_time)
            if cached is None:
                fetched = self.provider.fetch_factors(current_time)
                self.cache.set(fetched, current_time)
            else:
                fetched = cached
            factors = dict(fetched.factors)
            source = fetched.source
            observed_at = fetched.observed_at
            provider_reason = fetched.reason
        dxy = self.dxy_runtime.assess(factors)
        treasury = self.treasury_runtime.assess(factors)
        real_yield = self.real_yield_runtime.assess(factors)
        bias = self.bias_engine.evaluate(dxy, treasury, real_yield, [provider_reason])
        return MacroMarketFactorState(
            status="MACRO_MARKET_FACTOR_READY",
            source=source,
            observed_at=observed_at.isoformat(),
            dxy=dxy.as_dict(),
            treasury_yield=treasury.as_dict(),
            real_yield=real_yield.as_dict(),
            gold_market_bias=bias.as_dict(),
            raw_factors=factors,
            reason=bias.reason,
        )

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

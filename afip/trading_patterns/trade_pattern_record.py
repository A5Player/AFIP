"""Normalized trade pattern records for compact research storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _clean(value: str | None, default: str = "UNKNOWN") -> str:
    text = (value or default).strip().upper().replace(" ", "_")
    return text or default


@dataclass(frozen=True)
class TradePatternRecord:
    """Single normalized trading outcome used to update pattern repositories."""

    observed_at: datetime
    symbol: str = "GOLD#"
    position_direction: str = "NEUTRAL"
    market_regime: str = "UNKNOWN"
    session: str = "UNKNOWN"
    macro_bias: str = "NEUTRAL"
    institutional_bias: str = "NEUTRAL"
    liquidity_state: str = "BALANCED"
    volatility_bucket: str = "NORMAL"
    strategy_profile: str = "DAY_TRADE"
    entry_quality: float = 0.0
    result_amount: float = 0.0
    holding_minutes: float = 0.0
    mae_points: float = 0.0
    mfe_points: float = 0.0
    execution_cost_points: float = 0.0
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        observed_at = self.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        object.__setattr__(self, "observed_at", observed_at.astimezone(timezone.utc))
        object.__setattr__(self, "symbol", _clean(self.symbol, "GOLD#"))
        object.__setattr__(self, "position_direction", _clean(self.position_direction, "NEUTRAL"))
        object.__setattr__(self, "market_regime", _clean(self.market_regime))
        object.__setattr__(self, "session", _clean(self.session))
        object.__setattr__(self, "macro_bias", _clean(self.macro_bias, "NEUTRAL"))
        object.__setattr__(self, "institutional_bias", _clean(self.institutional_bias, "NEUTRAL"))
        object.__setattr__(self, "liquidity_state", _clean(self.liquidity_state, "BALANCED"))
        object.__setattr__(self, "volatility_bucket", _clean(self.volatility_bucket, "NORMAL"))
        object.__setattr__(self, "strategy_profile", _clean(self.strategy_profile, "DAY_TRADE"))
        object.__setattr__(self, "entry_quality", round(max(0.0, min(100.0, float(self.entry_quality))), 2))
        object.__setattr__(self, "result_amount", round(float(self.result_amount), 4))
        object.__setattr__(self, "holding_minutes", round(max(0.0, float(self.holding_minutes)), 2))
        object.__setattr__(self, "mae_points", round(abs(float(self.mae_points)), 4))
        object.__setattr__(self, "mfe_points", round(abs(float(self.mfe_points)), 4))
        object.__setattr__(self, "execution_cost_points", round(max(0.0, float(self.execution_cost_points)), 4))
        object.__setattr__(self, "tags", tuple(sorted(_clean(tag) for tag in self.tags if tag)))

    @property
    def pattern_key(self) -> str:
        parts = (
            self.symbol,
            self.position_direction,
            self.market_regime,
            self.session,
            self.macro_bias,
            self.institutional_bias,
            self.liquidity_state,
            self.volatility_bucket,
            self.strategy_profile,
        )
        return "|".join(parts)

    @property
    def setup_key(self) -> str:
        quality_bucket = int(self.entry_quality // 10) * 10
        tag_text = "+".join(self.tags) if self.tags else "NO_TAG"
        return f"{self.pattern_key}|Q{quality_bucket}|{tag_text}"

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "symbol": self.symbol,
            "position_direction": self.position_direction,
            "market_regime": self.market_regime,
            "session": self.session,
            "macro_bias": self.macro_bias,
            "institutional_bias": self.institutional_bias,
            "liquidity_state": self.liquidity_state,
            "volatility_bucket": self.volatility_bucket,
            "strategy_profile": self.strategy_profile,
            "entry_quality": self.entry_quality,
            "result_amount": self.result_amount,
            "holding_minutes": self.holding_minutes,
            "mae_points": self.mae_points,
            "mfe_points": self.mfe_points,
            "execution_cost_points": self.execution_cost_points,
            "tags": list(self.tags),
            "pattern_key": self.pattern_key,
            "setup_key": self.setup_key,
        }

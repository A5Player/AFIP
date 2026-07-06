"""Market-regime-first research dataset primitives.

The research platform keeps raw observations compact while preserving the
context needed for deterministic financial research.  Regime is part of the
primary grouping key so signal work never runs before market-state context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Iterable


def _normalize(value: str | None, default: str = "UNKNOWN") -> str:
    text = (value or default).strip().replace(" ", "_").replace("-", "_").upper()
    return text or default


@dataclass(frozen=True)
class ResearchSample:
    """Single compact outcome sample for research evaluation."""

    observed_at: datetime
    symbol: str = "GOLD#"
    market_regime: str = "UNKNOWN"
    direction: str = "FLAT"
    signal_family: str = "UNSPECIFIED"
    confidence: float = 0.0
    result_amount: float = 0.0
    execution_cost_points: float = 0.0
    holding_minutes: float = 0.0
    volatility_bucket: str = "UNKNOWN"
    source: str = "RUNTIME_OBSERVATION"

    def __post_init__(self) -> None:
        observed_at = self.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        object.__setattr__(self, "observed_at", observed_at.astimezone(timezone.utc))
        object.__setattr__(self, "symbol", _normalize(self.symbol, "GOLD#"))
        object.__setattr__(self, "market_regime", _normalize(self.market_regime))
        object.__setattr__(self, "direction", _normalize(self.direction, "FLAT"))
        object.__setattr__(self, "signal_family", _normalize(self.signal_family, "UNSPECIFIED"))
        object.__setattr__(self, "volatility_bucket", _normalize(self.volatility_bucket))
        object.__setattr__(self, "source", _normalize(self.source, "RUNTIME_OBSERVATION"))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "result_amount", float(self.result_amount))
        object.__setattr__(self, "execution_cost_points", float(self.execution_cost_points))
        object.__setattr__(self, "holding_minutes", float(self.holding_minutes))

    @property
    def regime_first_key(self) -> str:
        return "|".join(
            (
                self.market_regime,
                self.volatility_bucket,
                self.direction,
                self.signal_family,
                self.symbol,
            )
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "symbol": self.symbol,
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction": self.direction,
            "signal_family": self.signal_family,
            "confidence": self.confidence,
            "result_amount": self.result_amount,
            "execution_cost_points": self.execution_cost_points,
            "holding_minutes": self.holding_minutes,
            "source": self.source,
            "regime_first_key": self.regime_first_key,
        }


@dataclass
class ResearchDataset:
    """Deterministic in-memory research dataset grouped by regime first."""

    samples: list[ResearchSample] = field(default_factory=list)

    def add(self, sample: ResearchSample) -> None:
        self.samples.append(sample)
        self.samples.sort(key=lambda item: (item.regime_first_key, item.observed_at.isoformat()))

    def extend(self, samples: Iterable[ResearchSample]) -> None:
        for sample in samples:
            self.add(sample)

    def grouped(self) -> dict[str, list[ResearchSample]]:
        groups: dict[str, list[ResearchSample]] = {}
        for sample in self.samples:
            groups.setdefault(sample.regime_first_key, []).append(sample)
        return dict(sorted(groups.items()))

    def group_summary(self) -> list[dict[str, object]]:
        summaries: list[dict[str, object]] = []
        for key, values in self.grouped().items():
            wins = sum(1 for sample in values if sample.result_amount > 0)
            losses = sum(1 for sample in values if sample.result_amount < 0)
            gross_profit = sum(sample.result_amount for sample in values if sample.result_amount > 0)
            gross_loss = abs(sum(sample.result_amount for sample in values if sample.result_amount < 0))
            profit_factor = gross_profit if gross_loss == 0 else gross_profit / gross_loss
            summaries.append(
                {
                    "regime_first_key": key,
                    "observations": len(values),
                    "win_rate": round(wins / len(values) * 100, 4),
                    "losses": losses,
                    "expectancy": round(mean(sample.result_amount for sample in values), 4),
                    "average_confidence": round(mean(sample.confidence for sample in values), 4),
                    "average_execution_cost_points": round(
                        mean(sample.execution_cost_points for sample in values), 4
                    ),
                    "average_holding_minutes": round(mean(sample.holding_minutes for sample in values), 4),
                    "profit_factor": round(profit_factor, 4),
                }
            )
        return summaries

    def as_dict(self) -> dict[str, object]:
        return {
            "sample_count": len(self.samples),
            "group_count": len(self.grouped()),
            "groups": self.group_summary(),
        }

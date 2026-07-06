"""Market factor snapshot used by macro intelligence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketFactorSnapshot:
    """Latest macro market factors relevant to gold."""

    dxy_change_percent: float = 0.0
    us10y_change_bps: float = 0.0
    us02y_change_bps: float = 0.0
    real_yield_change_bps: float = 0.0
    gold_change_percent: float = 0.0
    silver_change_percent: float = 0.0
    oil_change_percent: float = 0.0
    equity_index_change_percent: float = 0.0

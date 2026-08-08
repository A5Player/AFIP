"""Closed-bar adverse-market behaviour labels for research and safety gates.

These labels describe observable OHLC behaviour only.  They never claim to
identify an institution, order book participant, or intent, and cannot grant
execution authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class AdversarialMarketBehaviour:
    timeframe: str
    threat_state: str
    pattern_name: str
    entry_policy: str
    confidence: float
    range_contraction_ratio: float | None
    candle_overlap_ratio: float | None
    sweep_side: str
    waiting_for: str
    reason: str
    research_only: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdversarialMarketBehaviourAnalyzer:
    """Detect only completed-bar compression and sweep proxies.

    Thresholds are deliberately conservative and are research labels, not a
    trading signal.  Missing history is explicit to preserve fail-closed use.
    """

    def __init__(self, minimum_bars: int = 20, recent_bars: int = 8) -> None:
        if minimum_bars < 20 or recent_bars < 4 or recent_bars >= minimum_bars:
            raise ValueError("invalid_adversarial_market_behaviour_window")
        self.minimum_bars = minimum_bars
        self.recent_bars = recent_bars

    @staticmethod
    def _overlap(rows: Sequence[tuple[float, float, float, float]]) -> float:
        comparisons = 0
        overlaps = 0
        for (_, high, low, _), (_, prior_high, prior_low, _) in zip(rows[1:], rows[:-1]):
            comparisons += 1
            if min(high, prior_high) > max(low, prior_low):
                overlaps += 1
        return overlaps / comparisons if comparisons else 0.0

    def analyze(self, bars: Sequence[Mapping[str, Any]], *, timeframe: str) -> AdversarialMarketBehaviour:
        rows: list[tuple[float, float, float, float]] = []
        for item in bars[-self.minimum_bars:]:
            values = tuple(_number(item.get(name)) for name in ("open", "high", "low", "close"))
            if any(value is None for value in values):
                continue
            open_, high, low, close = values
            if high >= low:
                rows.append((open_, high, low, close))
        key = str(timeframe or "UNKNOWN").upper()
        if len(rows) < self.minimum_bars:
            return AdversarialMarketBehaviour(key, "INSUFFICIENT_DATA", "ADVERSARIAL_CONTEXT_UNAVAILABLE", "WAIT", 0.0, None, None, "NONE", "minimum_closed_bar_history", "minimum_closed_bar_history_not_available")

        recent = rows[-self.recent_bars:]
        prior = rows[:-self.recent_bars]
        recent_range = sum(high - low for _, high, low, _ in recent) / len(recent)
        prior_range = sum(high - low for _, high, low, _ in prior) / len(prior)
        contraction = recent_range / max(prior_range, 1e-12)
        overlap = self._overlap(recent)
        prior_high = max(high for _, high, _, _ in prior)
        prior_low = min(low for _, _, low, _ in prior)
        _, latest_high, latest_low, latest_close = rows[-1]
        lower_sweep = latest_low < prior_low and latest_close >= prior_low
        upper_sweep = latest_high > prior_high and latest_close <= prior_high

        if lower_sweep or upper_sweep:
            side = "LOWER" if lower_sweep else "UPPER"
            return AdversarialMarketBehaviour(key, "POST_SWEEP_WAITING_CONFIRMATION", f"{side}_LIQUIDITY_SWEEP_PROXY", "WAIT", 75.0, round(contraction, 6), round(overlap, 6), side, "closed_bar_reclaim_and_retest_with_exact_research_rank", "sweep_proxy_detected_no_immediate_entry")
        if contraction <= 0.75 and overlap >= 0.55:
            return AdversarialMarketBehaviour(key, "SIDEWAY_COMPRESSION_NO_TRADE", "SIDEWAY_COMPRESSION", "BLOCK", 85.0, round(contraction, 6), round(overlap, 6), "NONE", "range_expansion_then_closed_bar_acceptance_and_exact_research", "range_contracting_with_high_candle_overlap")
        if latest_high > prior_high or latest_low < prior_low:
            return AdversarialMarketBehaviour(key, "BREAKOUT_UNCONFIRMED", "BREAKOUT_WITHOUT_ACCEPTANCE", "WAIT", 65.0, round(contraction, 6), round(overlap, 6), "NONE", "closed_bar_acceptance_then_retest_with_exact_research_rank", "boundary_break_requires_acceptance_confirmation")
        return AdversarialMarketBehaviour(key, "CLEAR", "NO_ADVERSE_PATTERN_DETECTED", "REVIEW", 50.0, round(contraction, 6), round(overlap, 6), "NONE", "normal_research_plan_gate", "no_configured_adverse_closed_bar_pattern_detected")

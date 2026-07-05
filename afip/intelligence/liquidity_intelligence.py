"""
AFIP Liquidity Intelligence.

Evaluates market liquidity conditions from OHLC data using financial market terminology.
This component is read-only and does not execute orders.
"""

from __future__ import annotations


class LiquidityIntelligence:
    """
    Detects liquidity conditions using equal highs, equal lows, sweep behavior,
    spread cost, and recent range quality.

    Output is designed for the AFIP Modular Intelligence pipeline:
    - direction: BUY, SELL, or FLAT
    - confidence: 0.0 to 100.0
    - status: READY, CAUTION, or LEARNING
    """

    name = "LiquidityIntelligence"

    def __init__(self, equality_tolerance_points: float = 50.0, sweep_lookback: int = 12):
        self.equality_tolerance_points = float(equality_tolerance_points)
        self.sweep_lookback = max(5, int(sweep_lookback))

    def analyze(self, snapshot: dict) -> dict:
        highs = [float(value) for value in snapshot.get("highs", []) if value is not None]
        lows = [float(value) for value in snapshot.get("lows", []) if value is not None]
        closes = [float(value) for value in snapshot.get("closes", []) if value is not None]
        spread = float(snapshot.get("spread", 999.0) or 999.0)

        if len(highs) < self.sweep_lookback or len(lows) < self.sweep_lookback or len(closes) < self.sweep_lookback:
            return self._result(
                direction="FLAT",
                confidence=30.0,
                status="LEARNING",
                reason="insufficient_liquidity_samples",
                liquidity_state="UNCONFIRMED",
                equal_highs=False,
                equal_lows=False,
                sweep_type="NONE",
                spread_points=spread,
            )

        recent_highs = highs[-self.sweep_lookback:]
        recent_lows = lows[-self.sweep_lookback:]
        recent_closes = closes[-self.sweep_lookback:]
        last_high = recent_highs[-1]
        last_low = recent_lows[-1]
        last_close = recent_closes[-1]

        previous_high = max(recent_highs[:-1])
        previous_low = min(recent_lows[:-1])

        equal_highs = self._has_equal_level(recent_highs[:-1], reference=previous_high)
        equal_lows = self._has_equal_level(recent_lows[:-1], reference=previous_low)

        buy_side_sweep = last_high > previous_high and last_close < previous_high
        sell_side_sweep = last_low < previous_low and last_close > previous_low

        direction = "FLAT"
        confidence = 42.0
        liquidity_state = "BALANCED_LIQUIDITY"
        reason = "liquidity_balanced"
        sweep_type = "NONE"

        if sell_side_sweep:
            direction = "BUY"
            confidence = 76.0
            liquidity_state = "SELL_SIDE_LIQUIDITY_SWEEP"
            reason = "sell_side_liquidity_sweep_rejection"
            sweep_type = "SELL_SIDE_SWEEP"
        elif buy_side_sweep:
            direction = "SELL"
            confidence = 76.0
            liquidity_state = "BUY_SIDE_LIQUIDITY_SWEEP"
            reason = "buy_side_liquidity_sweep_rejection"
            sweep_type = "BUY_SIDE_SWEEP"
        elif equal_lows and last_close > previous_low:
            direction = "BUY"
            confidence = 62.0
            liquidity_state = "SELL_SIDE_LIQUIDITY_POOL"
            reason = "equal_lows_liquidity_pool"
        elif equal_highs and last_close < previous_high:
            direction = "SELL"
            confidence = 62.0
            liquidity_state = "BUY_SIDE_LIQUIDITY_POOL"
            reason = "equal_highs_liquidity_pool"

        spread_penalty = self._spread_penalty(spread)
        range_penalty = self._range_penalty(recent_highs, recent_lows, last_close)
        confidence = max(0.0, confidence - spread_penalty - range_penalty)

        status = "READY"
        if spread_penalty >= 20.0 or range_penalty >= 15.0:
            status = "CAUTION"

        return self._result(
            direction=direction,
            confidence=round(confidence, 2),
            status=status,
            reason=reason,
            liquidity_state=liquidity_state,
            equal_highs=equal_highs,
            equal_lows=equal_lows,
            sweep_type=sweep_type,
            spread_points=spread,
            spread_penalty=round(spread_penalty, 2),
            range_penalty=round(range_penalty, 2),
            reference_high=round(previous_high, 3),
            reference_low=round(previous_low, 3),
        )

    def _has_equal_level(self, values: list[float], reference: float) -> bool:
        tolerance = self.equality_tolerance_points / 100.0
        touches = sum(1 for value in values if abs(value - reference) <= tolerance)
        return touches >= 2

    @staticmethod
    def _spread_penalty(spread_points: float) -> float:
        if spread_points <= 25.0:
            return 0.0
        if spread_points <= 35.0:
            return 8.0
        if spread_points <= 50.0:
            return 22.0
        return 35.0

    @staticmethod
    def _range_penalty(highs: list[float], lows: list[float], last_close: float) -> float:
        if last_close <= 0:
            return 15.0
        recent_range_pct = (max(highs) - min(lows)) / last_close * 100.0
        if recent_range_pct < 0.08:
            return 18.0
        if recent_range_pct < 0.15:
            return 8.0
        return 0.0

    @staticmethod
    def _result(**kwargs) -> dict:
        return {
            "name": LiquidityIntelligence.name,
            "direction": kwargs.get("direction", "FLAT"),
            "confidence": kwargs.get("confidence", 0.0),
            "status": kwargs.get("status", "READY"),
            "reason": kwargs.get("reason", "liquidity_evaluated"),
            "liquidity_state": kwargs.get("liquidity_state", "UNCONFIRMED"),
            "equal_highs": kwargs.get("equal_highs", False),
            "equal_lows": kwargs.get("equal_lows", False),
            "sweep_type": kwargs.get("sweep_type", "NONE"),
            "spread_points": kwargs.get("spread_points", 0.0),
            "spread_penalty": kwargs.get("spread_penalty", 0.0),
            "range_penalty": kwargs.get("range_penalty", 0.0),
            "reference_high": kwargs.get("reference_high"),
            "reference_low": kwargs.get("reference_low"),
        }

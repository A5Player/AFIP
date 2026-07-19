"""Deterministic capital-tier allocation without execution side effects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CapitalGrowthDecision:
    mode: str
    balance: float
    current_orders: int
    maximum_orders: int
    current_tier_minimum_balance: float | None
    target_lots: tuple[float, ...]
    available_lots: tuple[float, ...]
    next_tier_balance: float | None
    remaining_to_next_tier: float
    maximum_tier_balance: float | None
    withdrawal_reference_balance: float | None

    @property
    def target_total_lot(self) -> float:
        return round(sum(self.target_lots), 2)

    @property
    def available_total_lot(self) -> float:
        return round(sum(self.available_lots), 2)


class CapitalGrowthEngine:
    """Resolve configured capital tiers while preserving existing order slots."""

    @staticmethod
    def evaluate(
        *,
        mode: str,
        balance: float,
        current_orders: int,
        capital_tiers: Iterable[tuple[float, tuple[float, ...]]] = (),
        maximum_orders: int = 4,
        legacy_capital_per_unit: float = 1000.0,
        legacy_maximum_units: int = 1,
        lot_per_unit: float = 0.01,
    ) -> CapitalGrowthDecision:
        normalized_mode = str(mode).strip().upper()
        safe_balance = max(0.0, float(balance))
        safe_current_orders = max(0, int(current_orders))
        tiers = tuple((float(level), tuple(float(lot) for lot in lots)) for level, lots in capital_tiers)

        if safe_balance <= 0:
            return CapitalGrowthDecision(
                mode=normalized_mode,
                balance=safe_balance,
                current_orders=safe_current_orders,
                maximum_orders=max(0, int(maximum_orders)),
                current_tier_minimum_balance=None,
                target_lots=(),
                available_lots=(),
                next_tier_balance=tiers[0][0] if tiers else None,
                remaining_to_next_tier=max(0.0, tiers[0][0]) if tiers else 0.0,
                maximum_tier_balance=tiers[-1][0] if tiers else None,
                withdrawal_reference_balance=tiers[-1][0] if tiers else None,
            )

        if normalized_mode == "CAPITAL_TIER_TABLE":
            selected_level: float | None = None
            selected_lots: tuple[float, ...] = ()
            next_level: float | None = None
            for level, lots in tiers:
                if safe_balance >= level:
                    selected_level = level
                    selected_lots = lots
                else:
                    next_level = level
                    break
            available = selected_lots[safe_current_orders:max(0, int(maximum_orders))]
            return CapitalGrowthDecision(
                mode=normalized_mode,
                balance=safe_balance,
                current_orders=safe_current_orders,
                maximum_orders=max(0, int(maximum_orders)),
                current_tier_minimum_balance=selected_level,
                target_lots=selected_lots,
                available_lots=tuple(available),
                next_tier_balance=next_level,
                remaining_to_next_tier=round(max(0.0, (next_level or safe_balance) - safe_balance), 2) if next_level is not None else 0.0,
                maximum_tier_balance=tiers[-1][0] if tiers else None,
                withdrawal_reference_balance=tiers[-1][0] if tiers else None,
            )

        if normalized_mode == "RESEARCH_FIXED_001":
            return CapitalGrowthDecision(
                mode=normalized_mode,
                balance=safe_balance,
                current_orders=safe_current_orders,
                maximum_orders=0,
                current_tier_minimum_balance=None,
                target_lots=(float(lot_per_unit),),
                available_lots=(float(lot_per_unit),),
                next_tier_balance=None,
                remaining_to_next_tier=0.0,
                maximum_tier_balance=None,
                withdrawal_reference_balance=None,
            )

        # Legacy fixed-unit sizing is intentionally isolated from CAPITAL_TIER_TABLE.
        # Fail closed for invalid legacy values instead of dividing by zero.
        safe_legacy_capital = float(legacy_capital_per_unit)
        capital_units = (
            max(0, int(safe_balance // safe_legacy_capital))
            if safe_legacy_capital > 0.0
            else 0
        )
        capacity = max(0, int(legacy_maximum_units) - safe_current_orders)
        units = min(capital_units, capacity)
        lots = tuple(float(lot_per_unit) for _ in range(units))
        return CapitalGrowthDecision(
            mode="LEGACY_FIXED_UNIT",
            balance=safe_balance,
            current_orders=safe_current_orders,
            maximum_orders=int(legacy_maximum_units),
            current_tier_minimum_balance=None,
            target_lots=lots,
            available_lots=lots,
            next_tier_balance=None,
            remaining_to_next_tier=0.0,
            maximum_tier_balance=None,
            withdrawal_reference_balance=None,
        )

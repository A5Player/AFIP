"""Deterministic expansion of compact AFIP position-capacity formulas."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping


def _money(value: Decimal) -> float:
    integral = value.to_integral_value(rounding=ROUND_HALF_UP)
    return int(integral) if value == integral else float(value)


def _lot(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _explicit_ladder(raw: Mapping[str, Any]) -> tuple[tuple[float, tuple[float, ...]], ...]:
    rows = raw.get("tiers", ())
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("capital_tier_formula_explicit_tiers_required")
    result: list[tuple[float, tuple[float, ...]]] = []
    previous = Decimal("-1")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("capital_tier_formula_explicit_row_invalid")
        balance = Decimal(str(row.get("minimum_balance", "0")))
        lots_raw = row.get("lots", ())
        if balance <= previous:
            raise ValueError("capital_tier_formula_balances_not_ascending")
        if not isinstance(lots_raw, (list, tuple)) or not lots_raw:
            raise ValueError("capital_tier_formula_explicit_lots_required")
        lots = tuple(_lot(Decimal(str(value))) for value in lots_raw)
        if any(value <= 0 for value in lots):
            raise ValueError("capital_tier_formula_lot_range_invalid")
        result.append((_money(balance), lots))
        previous = balance
    return tuple(result)


def expand_capital_tier_formula(raw: Mapping[str, Any]) -> tuple[tuple[float, tuple[float, ...]], ...]:
    """Expand a compact formula into the legacy in-memory tier table.

    Compatibility fields such as ``one_order_minimum_balance`` remain readable,
    but ``authority_*`` fields are the sizing source of truth when supplied.
    """
    kind = str(raw.get("kind", "")).strip().upper()
    if kind == "EXPLICIT_LADDER":
        return _explicit_ladder(raw)

    lot_step = Decimal(str(raw.get("lot_step", "0.01")))
    maximum_lot = Decimal(str(raw.get("maximum_lot", "0")))

    one_balance = Decimal(str(raw.get(
        "authority_one_order_minimum_balance",
        raw.get("one_order_minimum_balance", "0"),
    )))
    two_balance = Decimal(str(raw.get(
        "authority_two_order_minimum_balance",
        raw.get("two_order_minimum_balance", "0"),
    )))
    three_balance = Decimal(str(raw.get(
        "authority_three_order_minimum_balance",
        raw.get("three_order_minimum_balance", "0"),
    )))

    if lot_step <= 0 or maximum_lot < lot_step:
        raise ValueError("capital_tier_formula_lot_range_invalid")
    steps_decimal = maximum_lot / lot_step
    if steps_decimal != steps_decimal.to_integral_value():
        raise ValueError("capital_tier_formula_maximum_lot_not_aligned")
    if not (one_balance < two_balance < three_balance):
        raise ValueError("capital_tier_formula_initial_balances_invalid")

    tiers: list[tuple[float, tuple[float, ...]]] = [
        (_money(one_balance), (_lot(lot_step),)),
        (_money(two_balance), (_lot(lot_step), _lot(lot_step))),
        (_money(three_balance), (_lot(lot_step), _lot(lot_step), _lot(lot_step))),
    ]

    maximum_steps = int(steps_decimal)
    previous_balance = three_balance
    for step_index in range(2, maximum_steps + 1):
        lot = lot_step * step_index
        if kind == "TRIANGULAR_BALANCE":
            multiplier = Decimal(str(raw.get("balance_multiplier", "0")))
            if multiplier <= 0:
                raise ValueError("capital_tier_formula_balance_multiplier_invalid")
            balance = multiplier * Decimal((step_index + 1) * (step_index + 2)) / Decimal(2)
        elif kind == "LINEAR_BALANCE":
            per_step = Decimal(str(raw.get("balance_per_lot_step", "0")))
            if per_step <= 0:
                raise ValueError("capital_tier_formula_balance_per_lot_step_invalid")
            balance = per_step * step_index
        else:
            raise ValueError("capital_tier_formula_kind_unknown")
        if balance <= previous_balance:
            raise ValueError("capital_tier_formula_balances_not_ascending")
        previous_balance = balance
        normalized_lot = _lot(lot)
        tiers.append((_money(balance), (normalized_lot, normalized_lot, normalized_lot)))

    return tuple(tiers)


def capital_tiers_from_profile(raw: Mapping[str, Any]) -> tuple[tuple[float, tuple[float, ...]], ...]:
    """Prefer legacy explicit tiers; otherwise expand the compact formula."""
    explicit = raw.get("capital_tiers", ())
    if explicit:
        return tuple(
            (float(item["minimum_balance"]), tuple(float(value) for value in item["lots"]))
            for item in explicit
        )
    formula = raw.get("capital_tier_formula")
    if formula:
        if not isinstance(formula, Mapping):
            raise ValueError("capital_tier_formula_must_be_mapping")
        return expand_capital_tier_formula(formula)
    return ()

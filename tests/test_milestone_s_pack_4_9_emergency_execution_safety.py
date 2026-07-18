from afip.execution_safety import (
    AllocationInput,
    ProtectionPlan,
    allocate_units,
    approve_execution,
    validate_protection_plan,
)


def test_maximum_units_is_ceiling_not_forced_target():
    result = allocate_units(
        AllocationInput(
            available_capital=650,
            free_margin=650,
            capital_per_unit=500,
            maximum_units=3,
            confidence_units=3,
            risk_units=3,
            margin_units=3,
        )
    )
    assert result.allowed is True
    assert result.allocated_units == 1


def test_insufficient_capital_blocks_all_units():
    result = allocate_units(
        AllocationInput(
            available_capital=650,
            free_margin=650,
            capital_per_unit=1000,
            maximum_units=3,
            confidence_units=3,
            risk_units=3,
            margin_units=3,
        )
    )
    assert result.allowed is False
    assert result.allocated_units == 0


def test_existing_exposure_reduces_capacity():
    result = allocate_units(
        AllocationInput(
            available_capital=5000,
            free_margin=5000,
            capital_per_unit=500,
            maximum_units=3,
            confidence_units=3,
            risk_units=3,
            margin_units=3,
            existing_exposure_units=2,
        )
    )
    assert result.allocated_units == 1


def test_fixed_500_tp_3000_sl_is_rejected():
    allowed, reason, _ = validate_protection_plan(
        ProtectionPlan(
            entry_price=4000.0,
            stop_loss_price=3970.0,
            take_profit_price=4005.0,
            point_size=0.01,
            side="BUY",
            sl_source="LEGACY_FIXED",
            tp_source="LEGACY_FIXED",
            planned_horizon="INTRADAY",
            minimum_reward_risk=0.0,
        )
    )
    assert allowed is False
    assert reason == "legacy_fixed_sl_tp_fallback_rejected"


def test_missing_adaptive_protection_blocks_order():
    decision = approve_execution(
        AllocationInput(
            available_capital=3000,
            free_margin=3000,
            capital_per_unit=1000,
            maximum_units=3,
            confidence_units=3,
            risk_units=3,
            margin_units=3,
        ),
        ProtectionPlan(
            entry_price=4000.0,
            stop_loss_price=None,
            take_profit_price=None,
            point_size=0.01,
            side="BUY",
        ),
    )
    assert decision.allowed is False
    assert decision.allocated_units == 0
    assert decision.reason == "protection_plan_unavailable"


def test_valid_adaptive_plan_uses_minimum_gate_capacity():
    decision = approve_execution(
        AllocationInput(
            available_capital=2600,
            free_margin=2400,
            capital_per_unit=1000,
            maximum_units=3,
            confidence_units=3,
            risk_units=2,
            margin_units=3,
        ),
        ProtectionPlan(
            entry_price=4000.0,
            stop_loss_price=3990.0,
            take_profit_price=4020.0,
            point_size=0.01,
            side="BUY",
            sl_source="MARKET_STRUCTURE",
            tp_source="NEXT_STRUCTURE_TARGET",
            planned_horizon="SWING",
            minimum_reward_risk=1.5,
        ),
    )
    assert decision.allowed is True
    assert decision.allocated_units == 2

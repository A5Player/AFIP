from afip.capital_growth_engine import CapitalGrowthEngine


P1 = (
    (0.0, (0.01,)),
    (200.0, (0.01, 0.01)),
    (450.0, (0.01, 0.01, 0.01)),
    (800.0, (0.01, 0.01, 0.01, 0.01)),
    (1250.0, (0.02, 0.01, 0.01, 0.01)),
    (1800.0, (0.02, 0.02, 0.01, 0.01)),
    (2450.0, (0.02, 0.02, 0.02, 0.01)),
    (3200.0, (0.02, 0.02, 0.02, 0.02)),
    (4050.0, (0.03, 0.02, 0.02, 0.02)),
    (5000.0, (0.03, 0.03, 0.02, 0.02)),
    (6050.0, (0.03, 0.03, 0.03, 0.02)),
    (7200.0, (0.03, 0.03, 0.03, 0.03)),
)


def evaluate(balance, current_orders=0):
    return CapitalGrowthEngine.evaluate(
        mode="CAPITAL_TIER_TABLE",
        balance=balance,
        current_orders=current_orders,
        capital_tiers=P1,
        maximum_orders=4,
    )


def test_current_and_next_tier_are_explainable():
    report = evaluate(612.0)
    assert report.current_tier_minimum_balance == 450.0
    assert report.target_lots == (0.01, 0.01, 0.01)
    assert report.next_tier_balance == 800.0
    assert report.remaining_to_next_tier == 188.0


def test_existing_orders_leave_only_remaining_slots():
    report = evaluate(1250.0, current_orders=2)
    assert report.target_lots == (0.02, 0.01, 0.01, 0.01)
    assert report.available_lots == (0.01, 0.01)


def test_maximum_tier_stops_risk_growth_and_exposes_withdrawal_reference():
    report = evaluate(10000.0)
    assert report.target_lots == (0.03, 0.03, 0.03, 0.03)
    assert report.next_tier_balance is None
    assert report.remaining_to_next_tier == 0.0
    assert report.maximum_tier_balance == 7200.0
    assert report.withdrawal_reference_balance == 7200.0


def test_research_mode_remains_one_fixed_001_per_approved_signal():
    report = CapitalGrowthEngine.evaluate(
        mode="RESEARCH_FIXED_001",
        balance=100.0,
        current_orders=99,
        maximum_orders=0,
    )
    assert report.available_lots == (0.01,)
    assert report.maximum_orders == 0


def test_legacy_mode_remains_backward_compatible():
    report = CapitalGrowthEngine.evaluate(
        mode="LEGACY_FIXED_UNIT",
        balance=300.0,
        current_orders=0,
        legacy_capital_per_unit=100.0,
        legacy_maximum_units=3,
    )
    assert report.available_lots == (0.01, 0.01, 0.01)

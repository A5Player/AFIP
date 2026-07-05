from afip.capital.allocation_policy import AllocationPolicy
from afip.capital.capital_allocator import CapitalAllocator
from afip.capital.capital_distribution import CapitalDistribution
from afip.capital.capital_reserve import CapitalReserve
from afip.capital.capital_utilization import CapitalUtilization
from afip.runtime.production_milestone_b_capital_runtime import ProductionMilestoneBCapitalRuntime


def _portfolio_equity():
    return {
        "status": "PORTFOLIO_EQUITY_READY",
        "account_count": 2,
        "total_equity": 2000.0,
        "total_net_asset_value": 2200.0,
    }


def _position_requests():
    return (
        {"account_id": "ACC1", "symbol": "GOLD#", "weight": 2.0},
        {"account_id": "ACC2", "symbol": "GOLD#", "weight": 1.0},
    )


def _policy():
    return {
        "minimum_reserve_ratio": 0.25,
        "maximum_allocation_ratio": 0.50,
        "maximum_utilization_ratio": 0.60,
    }


def test_capital_reserve_calculates_available_capital_after_reserve():
    result = CapitalReserve().calculate(_portfolio_equity(), _policy())
    assert result.status == "CAPITAL_RESERVE_READY"
    assert result.reserve_amount == 500.0
    assert result.available_capital == 1500.0
    assert result.ready is True


def test_capital_reserve_routes_unready_equity_to_review():
    result = CapitalReserve().calculate({"status": "PORTFOLIO_EQUITY_REVIEW", "total_equity": 2000.0}, _policy())
    assert result.status == "CAPITAL_RESERVE_REVIEW"
    assert result.reason == "portfolio_equity_not_ready"


def test_allocation_policy_accepts_allocation_within_limit():
    reserve = CapitalReserve().calculate(_portfolio_equity(), _policy())
    result = AllocationPolicy().evaluate(reserve, proposed_allocation=600.0, policy=_policy())
    assert result.status == "ALLOCATION_POLICY_READY"
    assert result.allocation_ratio == 0.4
    assert result.approved is True


def test_allocation_policy_rejects_allocation_above_limit():
    reserve = CapitalReserve().calculate(_portfolio_equity(), _policy())
    result = AllocationPolicy().evaluate(reserve, proposed_allocation=900.0, policy=_policy())
    assert result.status == "ALLOCATION_POLICY_REVIEW"
    assert result.reason == "allocation_ratio_above_limit"


def test_capital_distribution_splits_capital_by_position_weight():
    result = CapitalDistribution().distribute(600.0, _position_requests())
    assert result.status == "CAPITAL_DISTRIBUTION_READY"
    assert result.position_count == 2
    assert result.distributed_capital == 600.0
    assert result.allocations[0]["capital_amount"] == 400.0
    assert result.allocations[1]["capital_amount"] == 200.0


def test_capital_utilization_accepts_distribution_within_limit():
    reserve = CapitalReserve().calculate(_portfolio_equity(), _policy())
    distribution = CapitalDistribution().distribute(600.0, _position_requests())
    result = CapitalUtilization().evaluate(reserve, distribution, _policy())
    assert result.status == "CAPITAL_UTILIZATION_READY"
    assert result.utilization_ratio == 0.4
    assert result.within_limit is True


def test_capital_allocator_combines_failed_rules():
    summary = CapitalAllocator().allocate(_portfolio_equity(), 1200.0, _position_requests(), _policy())
    assert summary.status == "CAPITAL_ALLOCATION_REVIEW"
    assert summary.approved is False
    assert "allocation_ratio_above_limit" in summary.failed_rules
    assert "capital_distribution_not_ready" in summary.failed_rules


def test_production_milestone_b_capital_runtime_integrates_capital_controls():
    result = ProductionMilestoneBCapitalRuntime().run(
        portfolio_equity=_portfolio_equity(),
        proposed_allocation=600.0,
        position_requests=_position_requests(),
        capital_policy=_policy(),
    )
    assert result.status == "PRODUCTION_MILESTONE_B_CAPITAL_READY"
    assert result.capital_allocation_status == "CAPITAL_ALLOCATION_READY"
    assert result.reserve_status == "CAPITAL_RESERVE_READY"
    assert result.policy_status == "ALLOCATION_POLICY_READY"
    assert result.distribution_status == "CAPITAL_DISTRIBUTION_READY"
    assert result.utilization_status == "CAPITAL_UTILIZATION_READY"
    assert result.approved is True
    assert result.failed_rules == ()

from __future__ import annotations

from datetime import datetime, timezone

from afip.institutional.comex_inventory_runtime import ComexInventoryRuntime
from afip.institutional.cot_positioning import CotPositioningEngine
from afip.institutional.etf_gold_flow_runtime import EtfGoldFlowRuntime
from afip.institutional.institutional_positioning_consensus import InstitutionalPositioningConsensusEngine
from afip.institutional.institutional_positioning_runtime import InstitutionalPositioningRuntime
from afip.institutional.open_interest_runtime import OpenInterestRuntime
from afip.institutional.provider import EmptyInstitutionalDataProvider, StaticInstitutionalDataProvider
from afip.runtime.production_milestone_c_institutional_runtime import build_production_milestone_c_institutional_state


BASE_VALUES = {
    "managed_money_long": 180000,
    "managed_money_short": 90000,
    "commercial_long": 70000,
    "commercial_short": 130000,
    "open_interest": 520000,
    "open_interest_change": 4.2,
    "gold_price_change": 1.1,
    "etf_gold_tonnes_change": 6.0,
    "etf_value_change_usd": 650000000,
    "comex_registered_change": -3.8,
    "comex_eligible_change": -1.0,
}


def test_static_institutional_provider_returns_deterministic_values() -> None:
    observed_at = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
    provider = StaticInstitutionalDataProvider(BASE_VALUES, source="TEST_INSTITUTIONAL")

    result = provider.fetch_values(observed_at=observed_at)

    assert result.status == "INSTITUTIONAL_PROVIDER_READY"
    assert result.source == "TEST_INSTITUTIONAL"
    assert result.values["managed_money_long"] == 180000.0
    assert result.observed_at == observed_at


def test_empty_institutional_provider_is_safe_fallback() -> None:
    result = EmptyInstitutionalDataProvider().fetch_values(datetime(2026, 7, 6, 12, tzinfo=timezone.utc))

    assert result.status == "INSTITUTIONAL_PROVIDER_EMPTY"
    assert result.values == {}
    assert result.reason == "no_institutional_provider_configured"


def test_cot_positioning_scores_managed_money_net_long_as_supportive() -> None:
    state = CotPositioningEngine().assess_dict(BASE_VALUES)

    assert state["status"] == "COT_POSITIONING_READY"
    assert state["positioning_bias"] == "GOLD_SUPPORTIVE"
    assert state["managed_money_net"] == 90000
    assert state["confidence_score"] > 80


def test_cot_positioning_scores_managed_money_net_short_as_pressure() -> None:
    values = dict(BASE_VALUES, managed_money_long=50000, managed_money_short=160000)

    state = CotPositioningEngine().assess_dict(values)

    assert state["positioning_bias"] == "GOLD_PRESSURE"
    assert state["confidence_score"] > 80


def test_open_interest_runtime_detects_long_participation_expansion() -> None:
    state = OpenInterestRuntime().assess_dict(BASE_VALUES)

    assert state["status"] == "OPEN_INTEREST_READY"
    assert state["participation_state"] == "LONG_PARTICIPATION_EXPANDING"
    assert state["confidence_score"] > 70


def test_open_interest_runtime_detects_long_liquidation() -> None:
    values = dict(BASE_VALUES, open_interest_change=-5.0, gold_price_change=-1.5)

    state = OpenInterestRuntime().assess_dict(values)

    assert state["participation_state"] == "LONG_LIQUIDATION"
    assert state["confidence_score"] > 80


def test_etf_gold_flow_runtime_scores_inflow_as_supportive() -> None:
    state = EtfGoldFlowRuntime().assess_dict(BASE_VALUES)

    assert state["status"] == "ETF_GOLD_FLOW_READY"
    assert state["flow_bias"] == "GOLD_SUPPORTIVE"
    assert state["confidence_score"] > 60


def test_comex_inventory_runtime_flags_supply_tightening() -> None:
    state = ComexInventoryRuntime().assess_dict(BASE_VALUES)

    assert state["status"] == "COMEX_INVENTORY_READY"
    assert state["inventory_state"] == "AVAILABLE_SUPPLY_TIGHTENING"
    assert state["confidence_score"] > 60


def test_institutional_positioning_consensus_supportive_alignment() -> None:
    cot = CotPositioningEngine().assess_dict(BASE_VALUES)
    oi = OpenInterestRuntime().assess_dict(BASE_VALUES)
    etf = EtfGoldFlowRuntime().assess_dict(BASE_VALUES)
    comex = ComexInventoryRuntime().assess_dict(BASE_VALUES)

    state = InstitutionalPositioningConsensusEngine().combine_dict(cot, oi, etf, comex)

    assert state["status"] == "INSTITUTIONAL_POSITIONING_READY"
    assert state["positioning_bias"] == "GOLD_SUPPORTIVE"
    assert state["institutional_score"] > 65
    assert state["component_scores"]["cot_positioning"] > 80


def test_institutional_positioning_runtime_builds_ready_state() -> None:
    observed_at = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
    runtime = InstitutionalPositioningRuntime(StaticInstitutionalDataProvider(BASE_VALUES))

    state = runtime.run_dict(observed_at=observed_at)

    assert state["status"] == "INSTITUTIONAL_POSITIONING_RUNTIME_READY"
    assert state["observed_at"] == observed_at.isoformat()
    assert state["institutional_positioning"]["positioning_bias"] == "GOLD_SUPPORTIVE"


def test_production_milestone_c_institutional_runtime_is_deterministic() -> None:
    observed_at = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)

    first = build_production_milestone_c_institutional_state(BASE_VALUES, observed_at=observed_at)
    second = build_production_milestone_c_institutional_state(BASE_VALUES, observed_at=observed_at)

    assert first == second
    assert first["institutional_positioning"]["status"] == "INSTITUTIONAL_POSITIONING_READY"

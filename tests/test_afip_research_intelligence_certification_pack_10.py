from __future__ import annotations
import json
from pathlib import Path
from afip.research_data_foundation.intelligence import ResearchIntelligence, research_cluster_id, research_dimensions
from afip.research_data_foundation.aggregator import ResearchDatasetAggregator
from afip.research_data_foundation.dashboard import ResearchDashboardSnapshot


def case(case_id, *, profile="P1", pattern="BREAKOUT", regime="TREND", session="LONDON", timeframe="M15", profit=None):
    value={"trade_case_id":case_id,"profile_id":profile,"symbol":"GOLD#","decision_action":"BUY","market_context":{"pattern_id":pattern,"pattern_family":"MOMENTUM","market_regime":regime,"session":session,"timeframe":timeframe,"trend_context":"BULLISH","volatility_regime":"NORMAL"},"data_lineage":{"source":"test"},"lifecycle_state":"COMPLETE" if profit is not None else "ACTIVE","exit_context":{}}
    if profit is not None: value["exit_context"]={"net_profit":profit}
    return value


def write(root: Path, *cases):
    d=root/"trade_cases"; d.mkdir(parents=True)
    for item in cases: (d/f"{item['trade_case_id']}.json").write_text(json.dumps(item))


def test_cluster_is_profile_independent():
    assert research_cluster_id(case("A",profile="P1")) == research_cluster_id(case("B",profile="P4"))


def test_cluster_separates_regime_session_and_timeframe():
    base=case("A")
    assert research_cluster_id(base) != research_cluster_id(case("B",regime="RANGE"))
    assert research_cluster_id(base) != research_cluster_id(case("B",session="ASIA"))
    assert research_cluster_id(base) != research_cluster_id(case("B",timeframe="H1"))


def test_dimensions_do_not_include_profile():
    assert "profile_id" not in research_dimensions(case("A"))


def test_similarity_is_deterministic_and_weighted():
    a=case("A"); b=case("B"); c=case("C",pattern="REVERSAL",regime="RANGE")
    same=ResearchIntelligence.similarity(a,b)[0]
    different=ResearchIntelligence.similarity(a,c)[0]
    assert same == 100.0 and different < same


def test_nearest_uses_real_cases(tmp_path):
    write(tmp_path, case("A",profit=10), case("B",profit=-5), case("C",pattern="REVERSAL",profit=2))
    result=ResearchIntelligence(tmp_path).nearest(case("QUERY"))
    assert result["status"] == "READY"
    assert result["similarity_percent"] == 100.0
    assert result["historical_occurrences"] == 2
    assert result["completed_trades"] == 2
    assert result["win_rate"] == 50.0
    assert result["profit_factor"] == 2.0
    assert result["research_only"] and not result["affects_trading"]


def test_no_reference_case_is_fail_safe(tmp_path):
    result=ResearchIntelligence(tmp_path).nearest(case("QUERY"))
    assert result["status"] == "NO_REFERENCE_CASE"
    assert result["similarity_percent"] == 0.0


def test_aggregator_exposes_profile_independent_clusters(tmp_path):
    write(tmp_path, case("A",profile="P1",profit=10), case("B",profile="P4",profit=-5))
    result=ResearchDatasetAggregator(tmp_path).build()
    assert len(result["research_clusters"]) == 1
    assert result["research_clusters"][0]["occurrences"] == 2
    assert result["research_cluster_policy"].startswith("PROFILE_INDEPENDENT")


def test_dashboard_calculates_similarity_not_external_placeholder(tmp_path):
    write(tmp_path, case("A",profit=10))
    result=ResearchDashboardSnapshot(tmp_path).build({"current_market_case":case("Q"),"similarity_percent":1})
    assert result["similar_pattern_monitor"]["similarity_percent"] == 100.0
    assert result["similar_pattern_monitor"]["affects_trading"] is False


def test_unknown_context_does_not_crash():
    dims=research_dimensions({"symbol":"GOLD#","market_context":None})
    assert dims["pattern_id"] == "UNKNOWN"


def test_research_module_has_no_execution_imports():
    text=Path(__file__).parents[1].joinpath("afip/research_data_foundation/intelligence.py").read_text()
    assert "order_send" not in text and "MetaTrader5" not in text and "demo_execution_gateway" not in text

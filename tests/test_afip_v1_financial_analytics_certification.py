from __future__ import annotations
import json
from pathlib import Path
from afip.financial_intelligence_certification.runtime import FinancialAnalyticsCertificationRuntime

def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")

def test_cost_aware_portfolio_and_dimensions(tmp_path: Path):
    for i in range(1,5):
        _write(tmp_path/f"runtime/profiles/p{i}/financial_status.json", {
            "financial_connection_status":"CONNECTED","financial_data_source":"MT5",
            "financial_last_update":"2099-01-01T00:00:00Z","balance":1000,"equity":1005,
            "margin":10,"free_margin":995,"currency":"USD"})
    cases=[
      ("a",10.0,2.0,"P1","PAT_A","PLAN_A"),
      ("b",-4.0,-0.8,"P1","PAT_A","PLAN_A"),
      ("c",6.0,1.2,"P2","PAT_B","PLAN_B"),
    ]
    for cid,net,r,pid,pat,plan in cases:
        _write(tmp_path/f"runtime/research/trade_cases/{cid}.json", {
          "trade_case_id":cid,"profile_id":pid,"market_context":{"pattern_id":pat},
          "plan_context":{"plan_id":plan},"exit_context":{"research_feedback_status":"ELIGIBLE",
          "net_realized_profit_usd":net,"realized_r_multiple":r,"close_time":"2099-01-01T12:00:00Z"}})
    result=FinancialAnalyticsCertificationRuntime(tmp_path).evaluate()
    p=result["portfolio_performance"]
    assert p["net_realized_profit_usd"] == 12.0
    assert p["profit_factor"] == 4.0
    assert p["maximum_drawdown_usd"] == 4.0
    assert len(result["by_profile"]) == 2 and len(result["by_pattern"]) == 2 and len(result["by_plan"]) == 2
    assert result["affects_trading"] is False and result["execution_permission"] is False

def test_quarantined_and_gross_are_not_used(tmp_path: Path):
    _write(tmp_path/'runtime/research/trade_cases/q.json', {"trade_case_id":"q","exit_context":{
      "research_feedback_status":"QUARANTINED","gross_realized_profit_usd":999,"net_realized_profit_usd":999}})
    result=FinancialAnalyticsCertificationRuntime(tmp_path).evaluate()
    assert result["portfolio_performance"]["trade_count"] == 0
    assert result["portfolio_performance"]["net_realized_profit_usd"] == 0.0

def test_missing_series_does_not_manufacture_ratios(tmp_path: Path):
    _write(tmp_path/'runtime/research/trade_cases/a.json', {"trade_case_id":"a","exit_context":{
      "research_feedback_status":"ELIGIBLE","net_realized_profit_usd":5}})
    p=FinancialAnalyticsCertificationRuntime(tmp_path).evaluate()["portfolio_performance"]
    assert p["sharpe_ratio"] == "DATA_UNAVAILABLE"
    assert p["sortino_ratio"] == "DATA_UNAVAILABLE"

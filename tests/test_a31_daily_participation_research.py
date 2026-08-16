from afip.exit_evidence_research.a31_daily_participation import A31DailyParticipationResearch, DailySetupOutcome

def _item(name,day,score,result,partition="BLIND_FORWARD",orders=1):
    return DailySetupOutcome(name,f"2026-01-{day:02d}T10:00:00+00:00",partition,score,result,broker_order_count=orders,unit_count=orders)

def test_daily_limits_count_setups_not_split_broker_orders():
    rows=[_item("A",1,99,1,orders=3),_item("B",1,90,1),_item("C",1,80,-1),_item("D",1,70,-1)]
    results=A31DailyParticipationResearch().evaluate(rows)
    top3=next(x for x in results if x.partition=="BLIND_FORWARD" and x.policy_id=="TOP_0_TO_3")
    assert top3.selected_setups==3 and top3.broker_orders==5 and top3.units==5
    assert top3.win_rate_percent==66.666667 and top3.expectancy_r_per_setup==0.33333333

def test_dynamic_policy_can_skip_day_and_ranking_is_profile_neutral():
    rows=[_item("A",1,65,1),_item("B",2,98,2),_item("C",2,90,-1)]
    engine=A31DailyParticipationResearch();results=engine.evaluate(rows);ranked=engine.rank_blind_forward(results)
    dynamic=next(x for x in results if x.partition=="BLIND_FORWARD" and x.policy_id=="DYNAMIC_DAILY_BUDGET")
    assert dynamic.trading_days==1 and dynamic.no_trade_days==1
    assert ranked and all(x["profile_strategy_selection"]=="NOT_DECIDED" for x in ranked)
    assert all(x["execution_authority"]=="NONE" and x["automatic_research_promotion"] is False for x in ranked)

def test_future_data_at_decision_is_rejected():
    import pytest
    with pytest.raises(ValueError,match="future data"):
        DailySetupOutcome("X","2026-01-01T00:00:00+00:00","TRAIN",90,1,future_data_used_for_decision=True)

def test_dashboard_explains_units_and_full_policy_names(tmp_path):
    import json
    from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
    p=tmp_path/"runtime/research";p.mkdir(parents=True)
    item={"source_exit_policy_id":"ATR","research_rank":1,"policy_id":"TOP_0_TO_3","win_rate_percent":80,
      "expectancy_r_per_setup":.4,"net_result_r":4,"maximum_drawdown_r":1.2,"profit_factor_ratio":2,
      "selected_setups":10,"trading_days":5,"no_trade_days":2,"broker_orders":12,"units":12,
      "average_setups_per_calendar_day":1.43,"average_setups_per_trading_day":2}
    (p/"a31_daily_participation_rankings.jsonl").write_text(json.dumps({"record":item})+"\n",encoding="utf-8")
    html=SplitDashboardRenderer().render_research_html({},tmp_path)
    assert "A31 Daily Participation" in html and "80%" in html and "0.4 R/Setup" in html
    assert "Broker orders" in html and "ไม่เทรด 2 วัน" in html and "TOP_0_TO_3" in html

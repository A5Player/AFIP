from datetime import datetime, timezone
from afip.news_intelligence import NewsIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime

NOW=datetime(2026,7,10,3,0,tzinfo=timezone.utc)
def base(**extra):
    data={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"news_items":[]}
    data.update(extra); return data

def test_classifies_gold_news_and_reliability():
    r=NewsIntelligenceRuntime().evaluate_one(base(news_items=[{"headline":"Reuters: Fed turns dovish as lower yields support gold demand","source":"Reuters"}]))
    assert r.status=="READY" and r.gold_relevant_count==1 and r.high_reliability_count==1
    assert r.items[0].category=="CENTRAL_BANK" and r.items[0].sentiment=="BULLISH"

def test_detects_exact_normalized_duplicate():
    r=NewsIntelligenceRuntime().evaluate_one(base(news_items=[{"news_id":"A","headline":"Gold demand rises!","source":"Reuters"},{"news_id":"B","headline":"Gold demand rises","source":"Media"}]))
    assert r.duplicate_count==1 and r.unique_item_count==1 and r.items[1].duplicate_of=="A"

def test_low_reliability_social_news_requires_review():
    r=NewsIntelligenceRuntime().evaluate_one(base(news_items=[{"headline":"Gold rumor spreads","source":"Social"}]))
    assert r.items[0].reliability_score==0.35 and r.items[0].structured_signal=="REVIEW"

def test_news_never_allows_direct_execution():
    r=NewsIntelligenceRuntime().evaluate_one(base(news_items=[{"headline":"Gold demand rises","source":"Official"}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=NewsIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,news_items=[{"headline":"Gold update","source":"Reuters"}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_news_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",news_items=[{"headline":"Fed dovish, weak dollar supports gold","source":"Reuters"}]))
    panel=next(p for p in report.panels if p.panel_id=="news_intelligence")
    assert panel.title_en=="News Intelligence" and panel.title_th=="ปัญญาข่าวสาร"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)

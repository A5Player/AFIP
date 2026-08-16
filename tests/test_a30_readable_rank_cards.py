import json
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer

def test_a30_uses_readable_rank_cards_with_units_and_full_labels(tmp_path):
    p=tmp_path/"runtime/research";p.mkdir(parents=True)
    report={"row_count":1,"profile_strategy_selection":"NOT_DECIDED","execution_authority":"NONE","rows":[{
      "evidence_order":1,"pattern":"BREAKOUT ACCEPTANCE","timeframe":"H1","direction":"BUY","market_regime":"TREND",
      "entry_policy":"TOP RANKED","sl_atr_buffer":"ATR × 1.0 + 100 points","tp_atr_buffer":"ATR × 1.0 + 200 points",
      "holding_time":"8 closed H1 bars","samples":1000,"win_rate":80,"expectancy_r":.4,"profit_factor":2.1,
      "max_drawdown":4.2,"average_mfe_atr":1.8,"average_mae_atr":.7,"whipsaw_rate_percent":12,
      "walk_forward_status":"PASS","blind_forward_status":"PASS","evidence_tier":"ROBUST","reason":"blind-forward evidence passed"}]}
    (p/"a30_research_decision_matrix.json").write_text(json.dumps(report),encoding="utf-8")
    html=SplitDashboardRenderer().render_research_html({},tmp_path)
    for text in ("🏆 อันดับ 1","📈 BREAKOUT ACCEPTANCE","SL ATR±Buffer: ATR × 1.0 + 100 points",
                 "Win rate: 80%","Expectancy: 0.4 R/Setup","Drawdown: 4.2 R","Profit factor: 2.1 เท่า",
                 "📘 วิธีอ่านหน่วย","💡 สถานะ/เหตุผล"):
        assert text in html
    assert '<table><thead><tr><th>Order</th>' not in html

def test_a30_explains_missing_result_in_plain_thai(tmp_path):
    p=tmp_path/"runtime/research";p.mkdir(parents=True)
    (p/"a30_research_decision_matrix.json").write_text(json.dumps({"rows":[{"evidence_order":1,"pattern":"X"}]}),encoding="utf-8")
    html=SplitDashboardRenderer().render_research_html({},tmp_path)
    assert "ยังไม่มีผล Backtest จริง" in html

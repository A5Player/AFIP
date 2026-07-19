from pathlib import Path
from afip.dashboard_ui.launcher import default_dashboard_record
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _profiles():
    return [{
        "profile_id": f"P{i}", "profile_name": f"Profile {i}", "runtime_state":"RUNNING",
        "mt5_connection":"CONNECTED", "account":1000+i, "server":"XMGlobal-MT5 5",
        "account_balance":100.0*i, "account_equity":101.0*i, "free_margin":99.0*i,
        "currency":"USD", "data_fresh":True, "data_age_seconds":1,
    } for i in range(1,5)]


def test_default_record_has_no_invented_financial_values():
    record=default_dashboard_record()
    forbidden={"paper_balance","reserve","mt5_account_info","paper_orders","login"}
    assert forbidden.isdisjoint(record)
    assert record["financial_data_policy"]=="REAL_SOURCE_ONLY"


def test_dashboard_1_contains_real_finance_and_icons():
    html=ThreeDashboardRuntime().render_profiles_html({"profiles":_profiles()})
    assert "100.00" in html and "404.00" in html
    assert "💰" in html and "🏦" in html and "📈" in html
    assert 'http-equiv="refresh" content="5"' in html


def test_dashboard_1_missing_finance_is_not_zero_or_sample():
    profiles=[{"profile_id":f"P{i}","profile_name":"N/A","runtime_state":"STOPPED"} for i in range(1,5)]
    html=ThreeDashboardRuntime().render_profiles_html({"profiles":profiles})
    assert "DATA_UNAVAILABLE" in html
    assert "AFIP VPS Demo" not in html
    assert "12345678" not in html


def test_dashboard_2_and_3_are_separate(tmp_path:Path):
    runtime=ThreeDashboardRuntime()
    p1,p2,p3=runtime.write_three_dashboards({"profiles":_profiles()},tmp_path,tmp_path)
    assert p1.name=="afip_profiles_dashboard.html"
    assert p2.name=="afip_intelligence_engine_dashboard.html"
    assert p3.name=="afip_research_data_dashboard.html"
    assert "Research & Data" not in p2.read_text(encoding="utf-8").split("<h1>",1)[1].split("</h1>",1)[0]
    assert "Top 10 / Top 100" in p3.read_text(encoding="utf-8")


def test_research_rankings_use_real_records(tmp_path:Path):
    path=tmp_path/"runtime"/"research"/"events"; path.mkdir(parents=True)
    (path/"records.jsonl").write_text('\n'.join([
        '{"pattern_name":"A","market_regime":"TRENDING","outcome":"WIN"}',
        '{"pattern_name":"A","market_regime":"TRENDING","outcome":"LOSS"}',
        '{"pattern_name":"B","market_regime":"RANGING","outcome":"WIN"}',
    ]),encoding="utf-8")
    html=ThreeDashboardRuntime().render_research_html({"profiles":_profiles()},tmp_path)
    assert "A" in html and ">2<" in html
    assert "Open Top 100" in html

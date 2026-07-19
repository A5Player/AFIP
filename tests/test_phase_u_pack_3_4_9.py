from __future__ import annotations
import json
from pathlib import Path
from afip.financial_intelligence_certification import FinancialIntegrityRuntime, IntelligenceSourceCertificationRuntime
from afip.cross_market_gold_intelligence import CrossMarketGoldResearchRuntime
from afip.dashboard_ui.cross_market import render_cross_market_dashboard

def test_financial_runtime_never_invents_values(tmp_path:Path):
    report=FinancialIntegrityRuntime(tmp_path).evaluate()
    assert all(p["balance"]=="DATA_UNAVAILABLE" for p in report["profiles"])
    assert report["portfolio_total"]["equity"]=="DATA_UNAVAILABLE"

def test_verified_profile_requires_source_connection_and_timestamp(tmp_path:Path):
    p=tmp_path/"runtime/profiles/p1"; p.mkdir(parents=True)
    (p/"financial_status.json").write_text(json.dumps({"financial_data_source":"MT5:P1","financial_connection_status":"CONNECTED","financial_last_update":"2099-01-01T00:00:00Z","balance":123.45,"equity":125.0,"available_allocation":100.0}),encoding="utf-8")
    report=FinancialIntegrityRuntime(tmp_path).evaluate(); assert report["profiles"][0]["balance"]==123.45
    assert report["portfolio_total"]["balance"]=="DATA_UNAVAILABLE"

def test_intelligence_missing_snapshot_is_not_ready(tmp_path:Path):
    report=IntelligenceSourceCertificationRuntime(tmp_path).evaluate()
    assert report["verified_sources"]==0
    assert all(x["status"]=="DATA_UNAVAILABLE" for x in report["sources"])

def test_cross_market_config_is_research_only(tmp_path:Path):
    cfg=tmp_path/"config"; cfg.mkdir()
    (cfg/"cross_market_gold_intelligence.json").write_text(json.dumps({"sources":[],"gold_aliases":["GOLD#"]}),encoding="utf-8")
    report=CrossMarketGoldResearchRuntime(tmp_path).collect()
    assert report["execution_authority"] is False
    assert report["pipeline_stage"]=="RESEARCH_DATABASE"

def test_dashboard_displays_data_unavailable(tmp_path:Path):
    html=render_cross_market_dashboard(tmp_path)
    assert "DATA_UNAVAILABLE" in html and "Cross-Market Gold Intelligence" in html

def test_bank_runtime_has_no_1000_fallback():
    source=Path("afip/afip_bank_live/runtime.py").read_text(encoding="utf-8")
    assert 'paper_balance",1000.0' not in source
    assert "financial_source_not_verified" in source

def test_runtime_entrypoint_imports_afip_from_arbitrary_working_directory(tmp_path: Path):
    import subprocess
    import sys

    repository_root = Path(__file__).resolve().parents[1]
    script = repository_root / "tools" / "afip_phase_u_pack_3_4_9_runtime.py"
    runtime_root = tmp_path / "runtime_root"
    runtime_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(runtime_root),
            "--skip-cross-market",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "COMPLETE"
    assert payload["execution_authority"] is False

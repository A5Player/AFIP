import json
from pathlib import Path
from afip.portfolio_authority_certification import PortfolioMultiProfileAuthorityRuntime


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_verified_portfolio_totals_and_safety(tmp_path):
    profiles=[]
    for idx in range(1,5):
        profiles.append({"profile_id":f"P{idx}","status":"VERIFIED","currency":"USD","balance":1000.0,"equity":1010.0,"margin":10.0,"free_margin":1000.0,"available_allocation":900.0,"data_freshness":"FRESH"})
        write(tmp_path/f"runtime/profiles/p{idx}/portfolio_exposure.json", {"open_positions":[{"direction":"BUY","volume":0.01,"remaining_risk_usd":2.0,"profit":1.0}]})
    write(tmp_path/"runtime/certification/financial_integrity.json", {"profiles":profiles})
    result=PortfolioMultiProfileAuthorityRuntime(tmp_path).evaluate()
    assert result["status"] == "VERIFIED"
    assert result["portfolio_total"]["balance"] == 4000.0
    assert result["portfolio_total"]["buy_lots"] == 0.04
    assert result["portfolio_total"]["remaining_risk_usd"] == 8.0
    assert result["portfolio_total"]["portfolio_risk_percent_of_equity"] > 0
    assert result["affects_trading"] is False
    assert result["execution_permission"] is False
    assert result["automatic_allocation_change_allowed"] is False


def test_missing_profile_is_not_manufactured(tmp_path):
    write(tmp_path/"runtime/certification/financial_integrity.json", {"profiles":[{"profile_id":"P1","status":"VERIFIED","currency":"USD","balance":1}]})
    result=PortfolioMultiProfileAuthorityRuntime(tmp_path).evaluate()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["portfolio_total"]["balance"] == "DATA_UNAVAILABLE"
    assert "profile_financial_authority_incomplete" in result["authority_blockers"]


def test_currency_mismatch_blocks_verified_total(tmp_path):
    profiles=[]
    for idx in range(1,5):
        profiles.append({"profile_id":f"P{idx}","status":"VERIFIED","currency":"USD" if idx<4 else "THB","balance":100,"equity":100,"margin":0,"free_margin":100,"available_allocation":100})
        write(tmp_path/f"runtime/profiles/p{idx}/portfolio_exposure.json", {"open_positions":[]})
    write(tmp_path/"runtime/certification/financial_integrity.json", {"profiles":profiles})
    result=PortfolioMultiProfileAuthorityRuntime(tmp_path).evaluate()
    assert result["currency_consistent"] is False
    assert result["portfolio_total"]["currency"] == "DATA_UNAVAILABLE"
    assert result["status"] == "REVIEW_REQUIRED"

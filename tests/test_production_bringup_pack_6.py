from afip.afip_bank_live import AFIPBankLiveRuntime
from afip.dashboard_ui import DashboardUIRuntime

def base(**extra):
    data={"broker":"XM","symbol":"GOLD#","mode":"PAPER","initial_capital":1000,"reserve":100,"closed_profit":50,"floating_profit":25,"paper_trading_requested":False}
    data.update(extra); return data

def test_bank_calculates_capital_ledger():
    r=AFIPBankLiveRuntime().evaluate_one(base(deposits=200,withdrawals=100))
    assert r.status=="READY" and r.balance==1150 and r.equity==1175 and r.available_allocation==1075

def test_bank_accepts_transaction_records():
    r=AFIPBankLiveRuntime().evaluate_one(base(bank_transactions=[{"type":"DEPOSIT","amount":300},{"type":"WITHDRAWAL","amount":50}]))
    assert r.deposits==300 and r.withdrawals==50 and r.transaction_count==2

def test_bank_blocks_live_execution():
    r=AFIPBankLiveRuntime().evaluate_one(base(mode="LIVE",live_execution_enabled=True))
    assert r.status=="BLOCKED" and r.live_execution_enabled is False

def test_bank_enforces_xm_gold_policy():
    r=AFIPBankLiveRuntime().evaluate_one(base(broker="OTHER",symbol="SILVER"))
    assert "version1_xm_only_required" in r.validation_items and "version1_gold_only_required" in r.validation_items

def test_dashboard_contains_bilingual_bank_panel():
    report=DashboardUIRuntime().evaluate_one(base(deposits=100))
    panel=next(p for p in report.panels if p.panel_id=="afip_bank")
    assert panel.title_en=="AFIP Bank Live" and "ธนาคาร" in panel.title_th

def test_dashboard_html_explains_bank_values():
    html=DashboardUIRuntime().render_html(base(deposits=100,withdrawals=20))
    assert "Deposits" in html and "เงินฝาก" in html and "Withdrawals" in html and "เงินถอน" in html and "Live Execution: False" in html

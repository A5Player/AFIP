
from __future__ import annotations
import json
from pathlib import Path
from afip.research_data_foundation.runtime_collector import ResearchRuntimeCollector
from afip.research_data_foundation.dashboard import ResearchDashboardSnapshot


def _ledger(path: Path, *, pattern_id: str = "PAT-GOLD-1") -> None:
    payload = {"profile_id":"P1","symbol":"GOLD#","status":"ORDER_SENT","reason":"protected_demo_orders_sent",
        "checked_at_utc":"2026-07-29T10:00:00+00:00","decision_action":"BUY","decision_confidence":99.0,
        "tickets":[9001],"order_check_called":True,"order_send_called":True,"pattern_id":pattern_id}
    path.write_text(json.dumps(payload)+"\n", encoding="utf-8")


def test_closed_trade_preserves_signed_broker_costs_and_net_usd(tmp_path: Path) -> None:
    ledger=tmp_path/'ledger.jsonl'; _ledger(ledger)
    c=ResearchRuntimeCollector(tmp_path/'research'); c.ingest_ledgers([ledger])
    c.record_position_observation({"ticket":9001,"floating_profit":12.0,"observed_at_utc":"2026-07-29T10:10:00+00:00"})
    case=c.record_closed_trade({"ticket":9001,"realized_profit":10.0,"commission":-0.7,"swap":-0.2,"fee":-0.1,
        "initial_risk_usd":5.0,"exit_reason":"TAKE_PROFIT","observed_at_utc":"2026-07-29T10:30:00+00:00"})
    x=case['exit_context']
    assert x['net_realized_profit_usd'] == 9.0
    assert x['realized_r_multiple'] == 1.8
    assert x['outcome_class'] == 'WIN'
    assert x['research_feedback_status'] == 'ELIGIBLE'
    assert x['affects_trading'] is False


def test_exit_efficiency_and_profit_giveback_use_net_result(tmp_path: Path) -> None:
    ledger=tmp_path/'ledger.jsonl'; _ledger(ledger)
    c=ResearchRuntimeCollector(tmp_path/'research'); c.ingest_ledgers([ledger])
    c.record_position_observation({"ticket":9001,"floating_profit":20.0,"observed_at_utc":"2026-07-29T10:10:00+00:00"})
    case=c.record_closed_trade({"ticket":9001,"net_profit":15.0,"realized_profit":15.0,
        "exit_reason":"SMART_EXIT","observed_at_utc":"2026-07-29T10:30:00+00:00"})
    x=case['exit_context']
    assert x['exit_efficiency_ratio'] == 0.75
    assert x['profit_retained'] == 15.0
    assert x['profit_given_back'] == 5.0


def test_missing_money_result_is_quarantined_not_used_as_feedback(tmp_path: Path) -> None:
    ledger=tmp_path/'ledger.jsonl'; _ledger(ledger)
    c=ResearchRuntimeCollector(tmp_path/'research'); c.ingest_ledgers([ledger])
    case=c.record_closed_trade({"ticket":9001,"exit_reason":"UNKNOWN","observed_at_utc":"2026-07-29T10:30:00+00:00"})
    x=case['exit_context']
    assert x['outcome_data_quality'] == 'INCOMPLETE'
    assert 'money_result' in x['missing_outcome_fields']
    assert x['research_feedback_status'] == 'QUARANTINED'


def test_dashboard_summarizes_only_eligible_r_and_exit_efficiency(tmp_path: Path) -> None:
    ledger=tmp_path/'ledger.jsonl'; _ledger(ledger)
    c=ResearchRuntimeCollector(tmp_path/'research'); c.ingest_ledgers([ledger])
    c.record_position_observation({"ticket":9001,"floating_profit":10.0,"observed_at_utc":"2026-07-29T10:10:00+00:00"})
    c.record_closed_trade({"ticket":9001,"net_profit":8.0,"realized_profit":8.0,"initial_risk_usd":4.0,
        "exit_reason":"TAKE_PROFIT","observed_at_utc":"2026-07-29T10:30:00+00:00"})
    snap=ResearchDashboardSnapshot(tmp_path/'research').build()
    out=snap['closed_trade_outcome_feedback']
    assert out['closed_trade_count'] == 1
    assert out['eligible_feedback_count'] == 1
    assert out['net_realized_profit_usd'] == 8.0
    assert out['average_realized_r_multiple'] == 2.0
    assert out['average_exit_efficiency_ratio'] == 0.8
    assert out['affects_trading'] is False


def test_collector_has_no_execution_authority() -> None:
    import inspect
    source=inspect.getsource(ResearchRuntimeCollector)
    assert 'order_send(' not in source
    assert 'position_modify(' not in source

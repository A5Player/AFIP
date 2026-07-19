from pathlib import Path
from afip.mt5_historical_integration import *
from afip.runtime_standard_adapter import BackfillRequest, RuntimeStandardGuidance


class Gateway:
    def __init__(self, batches=None, symbols=("GOLD#", "EURUSD")):
        self.batches=list(batches or []); self.symbols=symbols; self.calls=0
    def available_symbols(self): return self.symbols
    def earliest_available(self, symbol, timeframe): return "2020-01-01T00:00:00+00:00"
    def latest_closed_bar(self, symbol, timeframe): return "2020-01-03T00:00:00+00:00"
    def fetch(self, symbol, timeframe, start, end, maximum_bars):
        if self.calls >= len(self.batches): return []
        value=self.batches[self.calls]; self.calls+=1; return value


def row(ts, next_ts):
    return {"timestamp_utc":ts,"next_start_utc":next_ts,"open":1,"high":2,"low":0,"close":1.5,"volume":10}


def guidance(usable=True):
    return RuntimeStandardGuidance("G","SELECTED_INITIAL_STANDARD","STD","1","POL",100,0,2,0.01,300,500,100,80,
        "TREND","EVIDENCE",("risk_approval","trading_cost_approval","profile_unit_capacity","execution_permission"),
        usable,"reason","evidence","2026-01-01")


def test_symbol_resolves_gold_alias():
    r=BrokerSymbolResolver().resolve("XAUUSD", ["GOLD#"])
    assert r.resolved_symbol=="GOLD#" and r.status=="RESOLVED"


def test_symbol_missing_blocks():
    r=BrokerSymbolResolver().resolve("GOLD#", ["EURUSD"])
    assert r.status=="NOT_FOUND"


def test_backfill_persists_and_checkpoints(tmp_path):
    g=Gateway([[row("2020-01-01T00:00:00+00:00","2020-01-02T00:00:00+00:00")],
               [row("2020-01-02T00:00:00+00:00","2020-01-04T00:00:00+00:00")]])
    result=ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("R","GOLD#","H1",maximum_bars_per_batch=10),g)
    assert result.status=="COMPLETED" and result.bars_persisted==2 and result.batches_completed==2
    assert (tmp_path/"historical_backfill_checkpoints.jsonl").exists()


def test_backfill_pause_and_resume(tmp_path):
    provider=ResumableMT5HistoricalProvider(tmp_path)
    first=provider.run(BackfillRequest("R","GOLD#","H1"),Gateway([[row("2020-01-01T00:00:00+00:00","2020-01-02T00:00:00+00:00")]]),maximum_batches=1)
    assert first.status=="PAUSED"
    second=provider.run(BackfillRequest("R","GOLD#","H1"),Gateway([[row("2020-01-02T00:00:00+00:00","2020-01-04T00:00:00+00:00")]]))
    assert second.resumed_from_checkpoint and second.status=="COMPLETED"


def test_backfill_deduplicates_existing_dataset(tmp_path):
    p=ResumableMT5HistoricalProvider(tmp_path)
    batch=[[row("2020-01-01T00:00:00+00:00","2020-01-04T00:00:00+00:00")]]
    p.run(BackfillRequest("A","GOLD#","H1"),Gateway(batch))
    result=p.run(BackfillRequest("B","GOLD#","H1"),Gateway(batch))
    assert result.duplicates_skipped==1 and result.bars_persisted==0


def test_provider_blocks_unavailable_symbol(tmp_path):
    result=ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("R","GOLD#","H1"),Gateway(symbols=("EURUSD",)))
    assert result.status=="BLOCKED"


def test_cursor_stall_blocks(tmp_path):
    result=ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("R","GOLD#","H1"),Gateway([[row("2020-01-01T00:00:00+00:00","2020-01-01T00:00:00+00:00")]]))
    assert result.status=="BLOCKED"


def test_trace_requires_every_existing_gate(tmp_path):
    trace=RuntimeDecisionTraceWriter(tmp_path).write(trace_id="T",profile_id="p1",symbol="GOLD#",action="BUY",
        guidance=guidance(),gate_states={"risk_approval":True,"trading_cost_approval":True,"profile_unit_capacity":True,"execution_permission":False})
    assert not trace.execution_allowed and trace.profile_id=="P1"


def test_trace_can_mark_gate_complete_without_sending_order(tmp_path):
    states={name:True for name in guidance().safety_gate_requirements}
    trace=RuntimeDecisionTraceWriter(tmp_path).write(trace_id="T",profile_id="P2",symbol="GOLD#",action="SELL",guidance=guidance(),gate_states=states)
    assert trace.execution_allowed and (tmp_path/"runtime_decision_traces.jsonl").exists()


def test_unusable_guidance_never_allows_execution(tmp_path):
    states={name:True for name in guidance().safety_gate_requirements}
    assert not RuntimeDecisionTraceWriter(tmp_path).write(trace_id="T",profile_id="P3",symbol="GOLD#",action="BUY",guidance=guidance(False),gate_states=states).execution_allowed


def test_dashboard_contract_matches_two_page_requirement():
    c=DashboardDataContract()
    assert c.operations_profiles==("P1","P2","P3","P4") and c.operations_page_refresh_seconds in range(5,11)
    assert c.intelligence_page_refresh_mode=="MANUAL" and c.preserve_scroll_on_manual_refresh


def test_dashboard_ranking_top10_top100(tmp_path):
    rows=[{"name":f"PATTERN-{i:03}","sample_size":100+i,"win_rate":50,"drawdown":i,"net_profit":i,"evidence_score":i} for i in range(120)]
    ranked=DashboardResearchRanking(tmp_path).rank(rows,ranking_id="R",category="pattern")
    assert len(ranked["top_10"])==10 and len(ranked["top_100"])==100 and ranked["hidden_record_count"]==20
    assert ranked["top_10"][0]["name"]=="PATTERN-119"


def test_dashboard_ranking_is_deterministic_on_ties(tmp_path):
    rows=[{"name":"B","evidence_score":1},{"name":"A","evidence_score":1}]
    assert [x["name"] for x in DashboardResearchRanking(tmp_path).rank(rows,ranking_id="R",category="situation")["top_10"]]==["A","B"]


def test_checksums_are_present(tmp_path):
    result=ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("R","GOLD#","H1"),Gateway([]))
    assert len(result.as_dict()["summary_checksum"])==64
    trace=RuntimeDecisionTraceWriter(tmp_path).write(trace_id="T",profile_id="P4",symbol="GOLD#",action="WAIT",guidance=guidance(False),gate_states={})
    assert len(trace.as_dict()["trace_checksum"])==64

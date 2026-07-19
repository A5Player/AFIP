from afip.research_replay_engine import ReplayEngine, ReplayPolicy

def test_future_profit_is_hidden_from_decision_function():
    seen = []
    def decide(event):
        seen.append(dict(event))
        return {"action": "BUY"}
    ReplayEngine().run([{"timestamp_utc": "2026-01-01T00:00:00Z", "future_profit": 5}], decide)
    assert "future_profit" not in seen[0]

def test_drawdown_limit_stops_replay():
    engine = ReplayEngine(ReplayPolicy(starting_equity=100, maximum_drawdown_percentage=10, stop_on_drawdown_limit=True))
    result = engine.run([{"future_profit": -20}, {"future_profit": 100}], lambda event: {"action": "BUY"})
    assert result["status"] == "STOPPED_DRAWDOWN_LIMIT"
    assert result["processed_event_count"] == 1

def test_wait_decision_has_no_profit_effect():
    result = ReplayEngine().run([{"future_profit": 100}], lambda event: {"action": "WAIT"})
    assert result["ending_equity"] == result["starting_equity"]

def test_replay_never_grants_execution_permission():
    result = ReplayEngine().run([], lambda event: {"action": "WAIT"})
    assert result["execution_permission"] is False

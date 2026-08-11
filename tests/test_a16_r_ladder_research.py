from afip.exit_outcome_research import RLadderResearch


def test_one_r_uses_verified_cost_not_one_r_lock():
    item = RLadderResearch.propose(direction="BUY", entry_price=100, current_price=103,
        current_stop_price=98, initial_risk_distance=2, maximum_favorable_r=1,
        verified_cost_distance=.1)
    assert item.status == "READY" and item.proposed_stop_price == 100.1 and item.locked_r == 0


def test_stop_never_widens():
    item = RLadderResearch.propose(direction="BUY", entry_price=100, current_price=110,
        current_stop_price=107, initial_risk_distance=2, maximum_favorable_r=3,
        verified_cost_distance=.1)
    assert item.status == "WAIT" and item.reason == "stop_must_only_tighten"


def test_broker_distance_blocks_unsafe_proposal():
    item = RLadderResearch.propose(direction="SELL", entry_price=100, current_price=98,
        current_stop_price=102, initial_risk_distance=2, maximum_favorable_r=1,
        verified_cost_distance=.1, minimum_stop_distance=2)
    assert item.status == "WAIT" and item.no_order_sent is True

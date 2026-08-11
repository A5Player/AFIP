"""Research-only R-ladder stop proposals; no execution authority."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RLadderProposal:
    status: str
    reason: str
    maximum_favorable_r: float
    proposed_stop_price: float
    locked_r: float
    stop_tightens_only: bool = True
    research_only: bool = True
    no_order_sent: bool = True


class RLadderResearch:
    """Derive an auditable candidate stop; it never modifies an order."""

    _STEPS = ((4.0, 3.0), (3.0, 2.0), (2.0, 1.0), (1.5, 0.25), (1.0, 0.0))

    @staticmethod
    def propose(*, direction: str, entry_price: float, current_price: float,
                current_stop_price: float, initial_risk_distance: float,
                maximum_favorable_r: float, verified_cost_distance: float,
                minimum_stop_distance: float = 0.0) -> RLadderProposal:
        if direction not in {"BUY", "SELL"} or min(entry_price, current_price, current_stop_price, initial_risk_distance) <= 0:
            return RLadderProposal("BLOCKED", "invalid_price_or_direction", maximum_favorable_r, current_stop_price, 0.0)
        if verified_cost_distance < 0 or minimum_stop_distance < 0:
            return RLadderProposal("BLOCKED", "invalid_cost_or_broker_distance", maximum_favorable_r, current_stop_price, 0.0)
        lock_r = next((lock for activation, lock in RLadderResearch._STEPS if maximum_favorable_r >= activation), None)
        if lock_r is None:
            return RLadderProposal("WAIT", "r_ladder_not_activated", maximum_favorable_r, current_stop_price, 0.0)
        if lock_r == 0.0:
            lock_distance = verified_cost_distance
        else:
            lock_distance = lock_r * initial_risk_distance + verified_cost_distance
        proposed = entry_price + lock_distance if direction == "BUY" else entry_price - lock_distance
        safe = proposed < current_price - minimum_stop_distance if direction == "BUY" else proposed > current_price + minimum_stop_distance
        tightens = proposed > current_stop_price if direction == "BUY" else proposed < current_stop_price
        if not safe:
            return RLadderProposal("WAIT", "broker_distance_or_noise_guard", maximum_favorable_r, current_stop_price, lock_r)
        if not tightens:
            return RLadderProposal("WAIT", "stop_must_only_tighten", maximum_favorable_r, current_stop_price, lock_r)
        return RLadderProposal("READY", "research_r_ladder_candidate", maximum_favorable_r, proposed, lock_r)

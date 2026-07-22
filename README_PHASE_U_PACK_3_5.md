# AFIP Phase U Pack 3.5
## Latest Lot & Position Authority Consolidation

This patch introduces one deterministic, side-effect-free sizing authority:
`afip.lot_authority.calculate_lot_authority`.

Contract:
- 1 unit is always 0.01 lot.
- Maximum 3 units per signal.
- Multiple units are separate 0.01 orders; never one 0.02/0.03 order.
- Approved units are the minimum of requested, confidence, capital, risk,
  profile maximum, and execution-safety gates.
- P3 below USD 200 remains eligible for one 0.01 unit when balance/equity are positive.
- The demo gateway consumes the authority result and cannot increase it.
- Existing capital tiers remain configuration inputs, not competing authorities.

Safety:
- Does not start execution.
- Does not change spread/trading-cost gates, SL/TP, intelligence, broker policy,
  credentials, or user runtime data.

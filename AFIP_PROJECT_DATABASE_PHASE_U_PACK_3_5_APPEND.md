
## Phase U Pack 3.5 — Latest Lot & Position Authority Consolidation

Introduced `afip.lot_authority.calculate_lot_authority` as the single deterministic sizing authority. Final units use the minimum of requested, confidence, capital, risk, profile maximum, and execution-safety gates. Every approved unit is a separate 0.01-lot order and total units cannot exceed three. P3 below USD 200 remains eligible for one 0.01 unit when capital is positive. Demo execution gateway now consumes this structured authority result and may not increase it. Execution remains operator-controlled and is not started by this pack.

# AFIP Milestone O Pack 4 — Learning Performance Evaluation

## Purpose

Evaluate accepted Pack 3 learning aggregates across isolated research datasets without granting adaptive, trading, knowledge-promotion, or execution authority.

## Scope

- Validate Pack 3 aggregate lineage and unique record IDs.
- Require an EVALUATION or HOLDOUT dataset.
- Validate chronology, data quality, future safety, sample sufficiency, numeric integrity, and locked Version 1.0 policy.
- Calculate deterministic weighted win/loss/breakeven rates, confidence, realized R, total R, payoff ratio, and training-versus-evaluation generalization gap.

## Safety

This pack cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY`, direct execution is false, live execution is disabled, and order status is `NO_ORDER_SENT`.

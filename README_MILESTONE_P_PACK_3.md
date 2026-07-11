# AFIP Milestone P Pack 3 — Market Behaviour Sequence Analysis

This patch adds deterministic, immutable, research-only analysis of chronological market-behaviour states produced by Milestone P Pack 2.

## Scope

- Validate Pack 2 normalized-state lineage.
- Require unique state IDs and at least three chronological states.
- Preserve Market Regime before Behaviour.
- Produce transition signatures and counts for regime, behaviour, and direction changes.
- Measure persistence and identify deterministic dominant regime and behaviour.
- Enforce certified data, future safety, XM only, GOLD# only, and 1 Unit = 0.01 Lot.

## Safety

The runtime cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`.

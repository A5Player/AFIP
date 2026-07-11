# AFIP Milestone P Pack 2 — Market Behaviour State Normalization

This patch normalizes accepted Milestone P Pack 1 market behaviour observations into one canonical, immutable research schema.

## Scope

- Validate Pack 1 observation lineage and READY status.
- Preserve Market Regime before Behaviour.
- Normalize direction, liquidity, regime, behaviour state, and bounded metrics.
- Derive deterministic directional strength, volatility state, range zone, and momentum state.
- Block uncertified data, future leakage, invalid chronology, invalid labels, non-finite or out-of-range metrics, and frozen-policy violations.

## Safety

This runtime is research-only. It cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY` with `NO_ORDER_SENT`.

# Milestone N Pack 3 — Portfolio Risk Engine

Adds a deterministic, research-only portfolio risk gate that aggregates current open-position risk and proposed risk. It validates portfolio risk budget, drawdown, margin level, total units, position lineage, independent position lifecycles, protected-runner exposure and permanent forbidden-method policy.

Execution remains `LOCKED_SIMULATION_ONLY`; no broker request or order is sent.

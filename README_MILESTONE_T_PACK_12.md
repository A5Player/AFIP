# AFIP Milestone T Pack 12

## Certified Trade Plan Runtime Orchestration

Pack 12 connects the selected research ranking and complete trade-plan certification to runtime capital capacity, restart/recovery reconciliation, auditable decision traces, and the P1-P4 Operations Dashboard read model.

## Locked authority order

1. Ranking must be eligible.
2. Complete Trade Plan must be certified.
3. Runtime capital capacity must still support the certified units.
4. MT5, data, account, positions, manual-order guard, equity, and runtime state must reconcile.
5. The result may only become `READY_FOR_EXECUTION_GATE_REVIEW`.
6. Existing Risk, Trading Cost, Position Policy, Demo/Live Permission, MT5 Order Check, and MT5 Order Send gates remain authoritative.

`execution_permission` is permanently `false` in this package.

## New append-only datasets

- `capital_capacity_snapshots`
- `recovery_reconciliations`
- `certified_plan_runtime_decisions`
- `profile_operations_read_models`

## Validation

- Focused tests: 16 passed
- Financial Naming: PASS
- Local Quality: PASS
- Full regression: 2284 passed
- Execution: LOCKED_SIMULATION_ONLY

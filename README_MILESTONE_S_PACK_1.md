# Milestone S Pack 1 — Locked Simulation Runtime Runner

Adds the operational runner required for continuous locked-simulation acceptance on Windows VPS.

## Command

```powershell
python afip.py run-locked-simulation
```

Optional controlled test:

```powershell
python afip.py run-locked-simulation 60 3
```

Arguments are `interval_seconds` and optional `maximum_cycles`.

## Safety

- Execution remains `LOCKED_SIMULATION_ONLY`.
- Direct execution remains disabled.
- Live execution remains disabled.
- Every cycle records `NO_ORDER_SENT`.
- No broker order API is called.
- Stop safely with `Ctrl+C`.

## Runtime records

- `runtime/locked_simulation/status.json`
- `runtime/locked_simulation/events.jsonl`
- `runtime/locked_simulation/acceptance_summary.json`

Identical consecutive decision snapshots are fingerprinted and not written twice.

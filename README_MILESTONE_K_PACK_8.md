# AFIP Milestone K Pack 8 — Execution Supervisor

Adds a deterministic supervisory layer that selects one highest-priority validated paper/demo instruction from execution-intelligence proposals.

## Scope
- Action conflict detection and priority resolution
- ENTRY, HOLD, STOP LOSS, TAKE PROFIT, TRAILING STOP, PARTIAL CLOSE, and EXIT supervision
- Position-state, fixed-unit, risk, timing, cost, market-structure, market-regime, and dependency validation
- English and Thai explainability
- Dashboard panel

## Safety Policy
- XM only
- GOLD# only
- 1 Unit = 0.01 lot
- LOCKED_SIMULATION_ONLY
- Direct execution disabled
- Live execution disabled
- NO_ORDER_SENT

## Validation
```powershell
pytest tests/test_milestone_k_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

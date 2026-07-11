# AFIP Milestone P Pack 6 — Market Behaviour Drift Detection

## Purpose

Detect deterministic market-behaviour drift between certified baseline and recent research segments using accepted Milestone P Pack 5 stability reports.

## Scope

The runtime compares:

- mean persistence ratio,
- mean market-regime change rate,
- mean behaviour-state change rate,
- stable-window rate,
- transition coverage,
- Pack 5 lineage,
- chronology and future safety.

It produces an immutable research report. It does not alter parameters, trading logic, positions, broker requests, or orders.

## Permanent Controls

- Broker: XM only
- Symbol: GOLD# only
- Base unit: 0.01 lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct execution: disabled
- Live execution: disabled
- Order status: NO_ORDER_SENT

## Validation

```powershell
pytest tests/test_milestone_p_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

# Milestone R Pack 5 — Production Repository Cleanup

## Purpose

Provides deterministic governance for narrowly scoped repository cleanup after Regression, Duplicate Code, Dead Code, and Architecture audits.

## Scope

- Validates Milestone R Pack 4 Architecture Audit lineage.
- Records reviewed cleanup actions using immutable evidence.
- Allows only reviewed non-source artifacts such as caches, generated artifacts, obsolete documents, and stale test artifacts.
- Retains protected compatibility or policy artifacts explicitly.
- Blocks incomplete actions, invalid chronology, duplicate IDs, protected-source cleanup attempts, and frozen-policy violations.
- Does not change trading logic, dependency wiring, execution, or Production Certification status.

## Execution Policy

- Broker: XM only
- Symbol: GOLD# only
- Base unit: 0.01 lot
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: disabled
- Live execution: disabled
- Order status: `NO_ORDER_SENT`

## Validation

```powershell
pytest tests/test_milestone_r_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Next

Milestone R Pack 6 — Safety Audit.

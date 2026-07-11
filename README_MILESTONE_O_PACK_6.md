# AFIP Milestone O Pack 6 — Learning Drift Detection

Deterministic, research-only drift detection after Pack 5 Learning Stability Validation.

## Scope
- Compare certified baseline and recent stability windows.
- Detect drift in mean evaluation realized R.
- Detect drift in mean generalization gap.
- Detect drift in positive evaluation-window rate.
- Validate unique Pack 5 lineage, chronology, sample coverage, data quality, future safety, and locked policy.

## Safety
This pack cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY`, Direct Execution is false, Live Execution is disabled, and order status is `NO_ORDER_SENT`.

## Validation
```powershell
pytest tests/test_milestone_o_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

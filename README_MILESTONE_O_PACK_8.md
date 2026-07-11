# AFIP Milestone O Pack 8 — Learning Validation Governance

## Purpose

This patch adds deterministic, research-only governance validation after Milestone O Pack 7 Learning Confidence Calibration.

## Scope

The runtime:

- accepts only READY and accepted Pack 7 confidence calibrations;
- validates unique lineage, chronology, data quality, and future safety;
- enforces Feature Freeze policy version integrity;
- enforces separation between research review and production-certification roles;
- checks minimum calibration count, sample coverage, and confidence thresholds;
- produces an immutable governance decision for documented manual review.

## Safety

The runtime has no authority to:

- update parameters automatically;
- change trading logic;
- promote production knowledge;
- modify positions;
- create broker requests;
- transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`.

## Validation

```powershell
pytest tests/test_milestone_o_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

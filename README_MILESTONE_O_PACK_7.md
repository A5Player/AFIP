# AFIP Milestone O Pack 7 — Learning Confidence Calibration

## Purpose

This patch adds deterministic, research-only confidence calibration after Milestone O Pack 6 Learning Drift Detection.

## Scope

The runtime:

- accepts only Pack 6 drift reports with READY status and no detected drift;
- validates unique lineage, chronology, data quality, and future safety;
- checks minimum report and sample coverage;
- combines raw confidence, evidence coverage, realized-R drift stability, generalization stability, and positive-window consistency;
- produces a bounded calibrated confidence score and confidence band;
- blocks insufficient or invalid evidence.

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
pytest tests/test_milestone_o_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

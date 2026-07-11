# AFIP Milestone Q Pack 3 — Market Intent Sequence Analysis

## Purpose
Adds deterministic, immutable analysis of chronological Market Intent State sequences produced by Milestone Q Pack 2.

## Scope
- Validate Pack 2 lineage and canonical schema.
- Enforce strictly increasing chronology and unique source state identifiers.
- Measure intent, direction, regime, and behaviour transitions.
- Calculate persistence, average intensity, intensity change, and continuation/reversal balance change.
- Classify persistent, reversal, breakout-development, liquidity-seeking, oscillating, or mixed sequences.

## Safety
This pack is research-only. It cannot update parameters, change trading logic, contact a broker, modify positions, or send orders. Execution remains `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`.

## Validation
```powershell
pytest tests/test_milestone_q_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

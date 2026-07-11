# AFIP Milestone Q Pack 4 — Market Intent Statistics

## Purpose
Adds deterministic and immutable statistical aggregation for accepted Market Intent Sequence reports from Milestone Q Pack 3.

## Scope
- Validate Pack 3 sequence lineage, unique identifiers, chronology, and count relationships.
- Aggregate observation and transition coverage.
- Calculate weighted persistence and weighted average intent intensity.
- Calculate intent, direction, regime, and behaviour change rates.
- Calculate mean intensity change, mean continuation/reversal balance change, and population standard deviation.
- Produce deterministic sequence-pattern distribution and dominant pattern.

## Safety
This pack is research-only. It cannot update parameters, change trading logic, contact a broker, modify positions, or send orders. Execution remains `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`.

## Validation
```powershell
pytest tests/test_milestone_q_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

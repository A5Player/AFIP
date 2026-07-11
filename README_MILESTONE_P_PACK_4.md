# AFIP Milestone P Pack 4 — Market Behaviour Transition Statistics

This patch aggregates certified Pack 3 market-behaviour sequence reports into immutable deterministic research statistics.

## Scope

- Transition frequency statistics
- Weighted persistence ratio
- Regime, behaviour, and direction change rates
- Dominant regime and behaviour state
- Pack 3 lineage and duplicate validation
- Chronology, data-quality, and future-safety gates
- Permanent Feature Freeze and execution lock validation

This component cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

## Validation

```powershell
pytest tests/test_milestone_p_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

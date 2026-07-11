# AFIP Milestone P Pack 5 — Market Behaviour Stability Validation

This patch validates certified Pack 4 transition-statistics reports across chronological research windows.

It measures persistence variability, regime-change variability, behaviour-change variability, dominant-state consistency, stable-window rate, and transition coverage. It blocks invalid lineage, duplicate reports, insufficient coverage, chronology errors, future leakage, uncertified data, invalid metrics, excessive variability, low consistency, and frozen-policy violations.

The component is immutable, deterministic, and research-only. It cannot update parameters, change trading logic, promote production knowledge, modify positions, contact a broker, or send an order.

## Validation

```powershell
pytest tests/test_milestone_p_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone P Pack 5 Market Behaviour Stability Validation"
git push
```

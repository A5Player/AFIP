# Milestone J Pack 4 — Opportunity Ranking Engine

Ranks GOLD# review opportunities after Market Regime, consensus, conflict, risk, and trading-cost gates. Ranking is deterministic, explainable, read-only, and never authorizes execution.

## Validation

```powershell
pytest tests/test_milestone_j_pack_4_opportunity_ranking.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

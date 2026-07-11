# AFIP Milestone O Pack 2 — Learning Evidence Normalization

## Purpose
Converts accepted immutable Milestone O Pack 1 learning records into deterministic canonical research evidence records.

## Normalized evidence
- Dataset role: TRAINING, EVALUATION, or HOLDOUT
- Outcome and direction
- Market Regime
- Confidence score
- Realized R
- Maximum favourable excursion in R
- Maximum adverse excursion in R
- Cost ratio
- Duration
- Sample weight

## Safety scope
- Requires Pack 1 accepted immutable lineage.
- Requires certified, chronological, future-safe evidence.
- Blocks non-finite and out-of-range metrics.
- Keeps dataset roles separated.
- No automatic parameter updates.
- No trading logic changes.
- No production knowledge promotion.
- No broker request, order transmission, or position modification.
- Execution remains `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`.

## Validation
```powershell
pytest tests/test_milestone_o_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone O Pack 2 Learning Evidence Normalization"
git push
```

# Production Milestone E Pack 2 — Volatility Intelligence

## Purpose

Pack E2 adds a deterministic volatility intelligence layer for AFIP. The pack converts market-regime-first volatility observations into data-derived volatility profiles and selects the strongest ready profile for downstream intelligence.

## Scope

- Volatility observation normalization
- Market-regime-first volatility grouping
- ATR, realized volatility, expected volatility, expansion, and compression profile metrics
- Data-derived volatility edge score
- Deterministic volatility policy
- Runtime report and entrypoint
- Production test coverage

## Quality

- Pack test: PASS
- Full pytest: PASS
- AFIP local quality check: PASS
- Financial naming validation: PASS

## Run

```powershell
pytest tests/test_production_milestone_e_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
```

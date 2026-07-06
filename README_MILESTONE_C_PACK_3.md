# AFIP Production Milestone C Pack 3 — News Intelligence Foundation

Patch type: incremental patch only.

## Purpose

Pack 3 adds the macro news foundation for AFIP. The goal is to prepare AFIP for free RSS, official-source feeds, and future paid news providers without changing the decision architecture.

## Added Capabilities

- Macro news provider contract
- Static deterministic news provider
- Empty safe fallback provider
- Combined provider for multi-source aggregation
- Macro news cache with TTL
- News impact scoring
- News urgency and confidence scoring
- Supportive / pressure / mixed gold bias classification
- Production Milestone C News Runtime
- Pack 3 tests and run scripts

## Data Storage Direction

AFIP should not store unlimited duplicate raw records forever. The intended production model is:

- Keep raw market/news/trade records only where audit or replay value is high
- Convert repeated patterns into compact counters and statistics
- Store occurrence count, win rate, expectancy, average MAE/MFE, drawdown, session, and regime summaries
- Keep provider timestamps and source confidence for data quality
- Use rolling archives for older high-frequency observations

This allows AFIP to build large market memory without excessive storage growth.

## Validation Commands

```powershell
pytest tests/test_production_milestone_c_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
```

## Git Commands

```powershell
git add .
git commit -m "Production Milestone C Pack 3"
git push
```

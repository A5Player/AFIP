# Production Milestone C Pack 9 — Provider Management and Data Quality Foundation

## Summary

Pack 9 adds a provider management layer for financial data inputs. It ranks data providers by health, latency, freshness, coverage, and reliability, then selects the best available source with safe fallback behavior.

## Added

- Provider health record model
- Provider quality scoring engine
- Provider registry and ranking
- Provider route selection with fallback
- Data quality assessment for normalized payloads
- Production Milestone C provider management runtime
- Pack 9 tests
- RUN scripts
- Quality result and project database updates

## Design Notes

The layer is provider-neutral. Free sources and paid sources can be added later through provider records and adapters without changing macro, institutional, or decision runtimes.

## Validation

```powershell
pytest tests/test_production_milestone_c_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
```

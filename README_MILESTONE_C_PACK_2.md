# AFIP Production Milestone C Pack 2

## Economic Calendar Integration

Pack 2 adds the production economic calendar integration layer for AFIP Macro Intelligence.

## Added

- Economic calendar provider contract
- Deterministic free-source provider adapter
- Empty provider fallback
- Calendar cache with TTL expiry
- Event countdown engine
- Market holiday and thin-liquidity detection
- Production calendar runtime
- Pack 2 tests
- Pack run scripts

## Runtime

```python
from afip.runtime.production_milestone_c_calendar_runtime import ProductionMilestoneCCalendarRuntime

runtime = ProductionMilestoneCCalendarRuntime()
state = runtime.run_dict(economic_events=[...])
```

## Validation

```powershell
pytest tests/test_production_milestone_c_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
git add .
git commit -m "Production Milestone C Pack 2"
git push
```

## Notes

This pack keeps AFIP independent from any single paid data provider. Live calendar data can be connected later through the provider contract without changing decision, risk, or portfolio logic.

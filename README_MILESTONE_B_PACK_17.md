# AFIP Production Milestone B — Pack 17

## Capital Allocation Layer

Pack 17 adds production-grade capital allocation controls for AFIP portfolio management. The package extends the Pack 15 equity layer and Pack 16 risk layer with capital reserve, allocation policy, weighted distribution, utilization assessment, and runtime integration.

## Added Components

- `afip/capital/capital_reserve.py`
- `afip/capital/allocation_policy.py`
- `afip/capital/capital_distribution.py`
- `afip/capital/capital_utilization.py`
- `afip/capital/capital_allocator.py`
- `afip/runtime/production_milestone_b_capital_runtime.py`
- `tests/test_production_milestone_b_pack_17.py`

## Production Rules

- Financial terminology only.
- No military naming.
- Deterministic dataclass outputs.
- Review routing when equity, policy, distribution, or utilization controls fail.
- Incremental patch only.

## Validation Commands

```powershell
pytest tests/test_production_milestone_b_pack_17.py -v
pytest
python tools/afip_local_quality_check.py
git add .
git commit -m "Production Milestone B Pack 17"
git push
```

## Expected Result

- Pack 17 tests: 8 passed
- Full pytest: 334 passed
- AFIP local quality check: PASS
- Financial naming validation: PASS

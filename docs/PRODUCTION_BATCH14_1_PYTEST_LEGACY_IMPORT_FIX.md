# Production Batch 14.1 — Pytest Legacy Import Fix

## Objective
Fix the remaining legacy test reference to the removed `aif` package.

## Changes
- Updated `tests/phase2/test_afip_intelligence_naming.py`
- Replaced legacy `aif.core` imports with official `afip.standards.financial_naming_standard` imports
- Added explicit regression checks to prevent reintroducing legacy `aif` imports

## Validation
Run:

```bash
python tools/afip_local_quality_check.py
```

Expected:
- Financial Naming Validation: PASS
- AFIP Simulation: PASS
- MT5 Data Check: PASS
- Pytest: PASS

## Notes
The `.pytest_cache` warning on Windows can be ignored if tests pass. If it blocks execution, delete `.pytest_cache` manually and rerun the check.

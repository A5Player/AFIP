# Production Milestone C Pack 18 — Execution Readiness

Pack 18 adds the Execution Readiness layer for AFIP Production Milestone C.

## Purpose

This pack converts enhanced decision output into a deterministic execution readiness state. It keeps the architecture data-first by checking cost, liquidity, risk, and capacity before execution readiness is allowed.

## Components

- `afip/execution_readiness/readiness_input.py`
- `afip/execution_readiness/readiness_checks.py`
- `afip/execution_readiness/readiness_policy.py`
- `afip/execution_readiness/execution_readiness_runtime.py`
- `afip/runtime/production_milestone_c_execution_readiness_runtime.py`
- `tests/test_production_milestone_c_pack_18.py`

## Validation

Run:

```powershell
pytest tests/test_production_milestone_c_pack_18.py -v
pytest
python tools/afip_local_quality_check.py
```

## Architecture Rules

- Financial terminology only
- Patch only
- Runtime deterministic
- Market regime and decision intelligence before execution readiness
- No hardcoded signal output values
- Cost, liquidity, risk, and capacity must be checked before execution readiness

# AFIP Production Milestone C Pack 14 — Research Platform

## Scope

Pack 14 adds a deterministic market-regime-first research platform for AFIP.  It converts compact outcome samples into grouped research datasets, evaluates research hypotheses with data-derived metrics, and exposes a production runtime entrypoint for review-ready research profiles.

## Production Rules

- Financial terminology only
- Market Regime before Signal
- Data First Architecture
- Knowledge First Architecture
- Deterministic runtime output
- Patch-only delivery
- No hardcoded learned market decisions

## Components

- `afip/research/research_dataset.py`
- `afip/research/research_hypothesis.py`
- `afip/research/research_platform_runtime.py`
- `afip/runtime/production_milestone_c_research_platform_runtime.py`
- `tests/test_production_milestone_c_pack_14.py`

## Validation

Run:

```powershell
pytest tests/test_production_milestone_c_pack_14.py -v
pytest
python tools/afip_local_quality_check.py
```

Or one command:

```powershell
.\RUN_MILESTONE_C_PACK_14.ps1
```

# Production Milestone E Pack 8 — Macro Context

## Purpose

Adds regime-first macro context intelligence for AFIP production intelligence. The pack evaluates DXY alignment, yield alignment, inflation surprise, labor market pressure, policy rate bias, news risk, macro consensus, and execution cost before selecting a deterministic macro context profile.

## Architecture

- Financial terminology only.
- Market regime before macro context.
- Data-derived metrics only.
- Deterministic runtime.
- Patch-only delivery.

## Validation

```powershell
pytest tests/test_production_milestone_e_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
```

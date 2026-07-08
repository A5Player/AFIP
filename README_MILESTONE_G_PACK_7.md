# Production Milestone G Pack 7 — Long-run Stability Testing

Pack 7 adds deterministic long-run stability testing for AFIP production hardening.

## Scope

- Evaluates repeated simulated runtime evidence.
- Verifies deterministic consistency across repeated runs.
- Reviews state integrity, resource trend quality, anomaly rate, and drawdown.
- Produces a long-run stability readiness report.
- Keeps live execution blocked and does not change trading decision logic.

## Architecture Rules

- Patch only.
- Production quality only.
- Financial terminology only.
- Market Regime before Signal Context.
- Deterministic runtime.
- No new AI decision layer.
- No live order creation.
- Backward compatible.

## Run

```powershell
pytest tests/test_production_milestone_g_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
```

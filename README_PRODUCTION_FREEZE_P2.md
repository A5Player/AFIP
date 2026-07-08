# Production Freeze P2 — Production Acceptance Test

Production Freeze P2 adds a deterministic Production Acceptance Test (PAT) layer.

The pack evaluates production-style scenario evidence before any real-money operation. It does not add a new AI layer, does not change trading decision logic, and does not enable live execution.

## Scope

- Production scenario acceptance review
- Market-regime-first acceptance evidence
- Simulation-only execution validation
- Spread, margin, data continuity, engine agreement, confidence, risk gate, and decision consistency scoring
- Acceptance gate reporting

## Runtime Entry Point

`afip/runtime/production_freeze_p2_acceptance_test_runtime.py`

## Test

`tests/test_production_freeze_p2_acceptance_test.py`

## Validation

```powershell
pytest tests/test_production_freeze_p2_acceptance_test.py -v
pytest
python tools/afip_local_quality_check.py
```

## Production Rules

- Patch Only
- Production Quality Only
- Financial terminology only
- No live execution enabled
- No trading logic changed
- Market Regime before Signal Context
- Deterministic Runtime

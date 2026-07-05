# AFIP Production Milestone B Pack 6

## Name

Market Context Engine

## Purpose

This pack adds market context assessment before unified decision runtime. It identifies trend, range, breakout, pullback, volatility, liquidity, and transition context using deterministic production-safe logic.

## Files

- `afip/context/__init__.py`
- `afip/context/market_state_classifier.py`
- `afip/context/volatility_context.py`
- `afip/context/liquidity_context.py`
- `afip/context/context_transition_model.py`
- `afip/context/market_context_engine.py`
- `afip/runtime/production_milestone_b_context_runtime.py`
- `docs/PRODUCTION_MILESTONE_B_PACK_6.md`
- `tests/test_production_milestone_b_pack_6.py`

## Validation

```powershell
pytest tests/test_production_milestone_b_pack_6.py
python tools/afip_local_quality_check.py
```

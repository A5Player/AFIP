# Production Milestone B Pack 15 — Portfolio Equity Layer

Pack 15 adds the production portfolio equity layer after Approval, Settlement, Accounting, and Valuation.

## Scope

- Equity snapshot calculation
- Net Asset Value calculation
- Portfolio equity aggregation
- Equity reconciliation controls
- Production equity runtime integration

## Runtime

`afip/runtime/production_milestone_b_equity_runtime.py`

## Source

- `afip/portfolio/equity_snapshot.py`
- `afip/portfolio/equity_calculator.py`
- `afip/portfolio/net_asset_value.py`
- `afip/portfolio/portfolio_equity.py`
- `afip/portfolio/equity_reconciliation.py`
- `afip/portfolio/__init__.py`

## Tests

`tests/test_production_milestone_b_pack_15.py`

## Run Commands

```powershell
pytest tests/test_production_milestone_b_pack_15.py -v
pytest
python tools/afip_local_quality_check.py
git add .
git commit -m "Production Milestone B Pack 15"
git push
```

## Expected Result

- Pack 15 tests: 8 passed
- Full pytest: 318 passed
- Financial naming validation: PASS
- Local quality check: PASS

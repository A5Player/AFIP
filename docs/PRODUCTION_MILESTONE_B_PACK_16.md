# Production Milestone B Pack 16 — Portfolio Risk Layer

Pack 16 adds portfolio risk controls above the Pack 15 portfolio equity layer.

## Scope

- Risk budget evaluation against total portfolio equity
- Gross exposure limit evaluation
- Position concentration risk evaluation
- Portfolio risk summary
- Production runtime integration
- AFIP project database update

## Runtime

```python
from afip.runtime.production_milestone_b_risk_runtime import ProductionMilestoneBRiskRuntime

result = ProductionMilestoneBRiskRuntime().run(
    portfolio_equity={"status": "PORTFOLIO_EQUITY_READY", "total_equity": 2000.0},
    proposed_risk_amount=40.0,
    positions=(
        {"symbol": "GOLD#", "market_value": 500.0},
        {"symbol": "GOLD#", "market_value": 300.0},
    ),
    risk_limits={
        "maximum_risk_ratio": 0.03,
        "maximum_exposure_ratio": 0.75,
        "maximum_position_ratio": 0.55,
    },
)
```

## Validation

```powershell
pytest tests/test_production_milestone_b_pack_16.py -v
pytest
python tools/afip_local_quality_check.py
```

Expected result after Pack 16:

- Pack 16 test: 8 passed
- Full pytest: 326 passed
- AFIP local quality check: PASS

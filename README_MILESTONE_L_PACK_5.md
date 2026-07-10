# Milestone L Pack 5 — Paper Performance Analytics

## Purpose
Aggregate only accepted Milestone L Pack 4 paper outcomes into deterministic, auditable performance statistics without changing trading logic or transmitting an order.

## Included analytics
- Eligible and rejected outcome counts
- Win, loss, and break-even counts
- Win rate
- Gross profit, gross loss, and net profit
- Profit factor
- Average realized R and expectancy R
- Maximum drawdown from chronological net outcomes
- Trading cost, swap cost, and cost-to-gross-profit ratio
- Minimum sample sufficiency
- Future-information and incomplete-data exclusion
- Independent position lifecycle and protected-runner exposure validation
- English and Thai dashboard explainability

## Permanent policies
- XM only
- GOLD# only
- 1 Unit = 0.01 lot
- Traditional DCA disabled
- Averaging down disabled
- Martingale disabled
- Grid trading disabled
- Protected runners remain included in total exposure and risk
- LOCKED_SIMULATION_ONLY
- Direct execution disabled
- Live execution disabled
- NO_ORDER_SENT

## Validation
```powershell
pytest tests/test_milestone_l_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone L Pack 5 Paper Performance Analytics"
git push
```

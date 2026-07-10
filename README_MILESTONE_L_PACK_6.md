# Milestone L Pack 6 — Paper Performance Certification

This incremental patch certifies the Paper Performance Analytics baseline produced by Milestone L Pack 5.

## Scope

- Pack 5 analytics linkage
- Minimum sample certification
- Expectancy threshold
- Profit-factor threshold
- Maximum drawdown threshold
- Maximum cost-ratio threshold
- Positive net-profit requirement
- Data-integrity certification
- Future-leakage and incomplete-data controls
- Independent position lifecycle
- Protected runner exposure inclusion
- No Traditional DCA or averaging down
- Shadow-observation readiness only
- Demo and live execution remain disabled
- Dashboard explainability in English and Thai

## Permanent policies

- Broker: XM only
- Symbol: GOLD# only
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: Disabled
- Order Status: NO_ORDER_SENT

## Validation

```powershell
pytest tests/test_milestone_l_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone L Pack 6 Paper Performance Certification"
git push
```

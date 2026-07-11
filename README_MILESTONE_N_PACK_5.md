# Milestone N Pack 5 — Portfolio Exposure Coordination

This incremental patch validates portfolio exposure after Milestone N Pack 4 Capital Allocation.

It coordinates allocated BUY/SELL units, total risk, direction concentration and Protected Runner exposure across independent Trade Plans. The runtime is deterministic, research-only and has no broker or order-transmission authority.

## Locked production policy

- Broker: XM only
- Symbol: GOLD# only
- Base Unit: 0.01 lot
- Traditional DCA, Averaging Down, Martingale, Grid Trading and Recovery Trading remain prohibited
- Execution remains `LOCKED_SIMULATION_ONLY`
- Direct execution remains disabled
- Order status remains `NO_ORDER_SENT`

## Validation

```powershell
pytest tests/test_milestone_n_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone N Pack 5 Portfolio Exposure Coordination"
git push
```

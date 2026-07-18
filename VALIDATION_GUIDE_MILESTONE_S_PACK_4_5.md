# Validation Guide — Milestone S Pack 4.5

```powershell
pytest tests\test_milestone_s_pack_4.py
pytest
python tools\afip_local_quality_check.py
python afip.py mt5-check
python -m afip.dashboard_ui
```

After VPS deployment, stop and restart all P1-P4 demo runtime processes so they load the new policy.
Verify `allocation_mode`, `capital_tier_step`, `maximum_orders`, `order_unit_distribution`, and `total_lot` in each profile state file.

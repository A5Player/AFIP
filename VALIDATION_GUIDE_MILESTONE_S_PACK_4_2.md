# Validation Guide — Milestone S Pack 4.2

Run from `C:\AFIP\source` after stopping the four demo runners.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "C:\AFIP\source"

python tools\afip_demo_execution_control.py stop-all
pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_1.py
pytest
python tools\afip_local_quality_check.py
python afip.py mt5-check
python -m afip.dashboard_ui
python tools\afip_demo_execution_control.py start-all
python tools\afip_demo_execution_control.py status
```

Inspect one profile state and ledger:

```powershell
Get-Content .\runtime\profiles\p1\demo_execution_state.json
Get-Content .\runtime\profiles\p1\logs\demo_execution_ledger.jsonl -Tail 5
```

Expected diagnostic fields include:

- `trading_cost_status`
- `trading_cost_allowed`
- `spread_points`
- `caution_spread_points`
- `max_spread_points`
- `point_size`
- `digits`
- `order_check_called`
- `order_send_called`
- `mt5_result_code`
- `mt5_result_comment`

A market-based `WAITING` result remains valid when `allowed=False`. A `CAUTION` result with `allowed=True` must no longer be rejected only because its status is not `PASS`.

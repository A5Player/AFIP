$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone S Pack 3 ==="
python -m pytest tests/test_milestone_s_pack_3.py -v
python -m pytest -q
python tools/afip_local_quality_check.py
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P4 --reconnect-attempts 2
python -m afip.dashboard_ui
Write-Host "Pack 3 validation completed. LOCKED_SIMULATION_ONLY / NO_ORDER_SENT"

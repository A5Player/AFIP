$ErrorActionPreference = "Stop"
python -m pytest tests/test_milestone_s_pack_4.py -v
python -m pytest -q
python tools/afip_local_quality_check.py
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P2 P3 P4 --reconnect-attempts 2
python tools/afip_demo_execution_control.py status
python -m afip.dashboard_ui
Write-Host "Milestone S Pack 4 validation completed. Validation does not arm or send demo orders."

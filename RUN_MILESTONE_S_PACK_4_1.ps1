$ErrorActionPreference = "Stop"
python -m pytest tests/test_milestone_s_pack_4_1.py -v
python -m pytest -q
python tools/afip_local_quality_check.py
python tools/afip_dashboard_live_control.py start
python tools/afip_dashboard_live_control.py status
python -m afip.dashboard_ui
Write-Host "Dashboard: runtime\dashboard\afip_dashboard.html"

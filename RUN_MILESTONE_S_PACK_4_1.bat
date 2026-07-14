@echo off
python -m pytest tests/test_milestone_s_pack_4_1.py -v || exit /b 1
python -m pytest -q || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python tools\afip_dashboard_live_control.py start || exit /b 1
python tools\afip_dashboard_live_control.py status || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Dashboard: runtime\dashboard\afip_dashboard.html

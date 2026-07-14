@echo off
python -m pytest tests/test_milestone_s_pack_4.py -v || exit /b 1
python -m pytest -q || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P2 P3 P4 --reconnect-attempts 2 || exit /b 1
python tools/afip_demo_execution_control.py status || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone S Pack 4 validation completed. Validation does not arm or send demo orders.

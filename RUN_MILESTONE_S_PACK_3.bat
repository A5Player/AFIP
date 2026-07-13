@echo off
python -m pytest tests/test_milestone_s_pack_3.py -v || exit /b 1
python -m pytest -q || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python tools\afip_mt5_multi_terminal_check.py --profiles P1 P4 --reconnect-attempts 2
python -m afip.dashboard_ui || exit /b 1
echo Pack 3 validation completed. LOCKED_SIMULATION_ONLY / NO_ORDER_SENT

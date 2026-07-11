@echo off
setlocal
pytest tests/test_milestone_q_pack_9.py -v || exit /b 1
pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
endlocal

@echo off
setlocal
python -m pytest tests/test_milestone_s_pack_5_1.py tests/test_milestone_s_pack_5_2.py || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo === Pack 5.2 validation completed ===
endlocal

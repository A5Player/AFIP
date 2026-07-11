@echo off
setlocal

echo === AFIP Milestone Q Pack 4 — Market Intent Statistics ===
python -m pytest tests/test_milestone_q_pack_4.py -v || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone Q Pack 4 validation completed.
endlocal

@echo off
setlocal

echo === AFIP Milestone R Pack 1 — Production Regression Audit ===
python -m pytest tests/test_milestone_r_pack_1.py -v || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo === Milestone R Pack 1 validation completed ===
echo Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT
endlocal

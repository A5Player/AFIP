@echo off
setlocal

echo === AFIP Milestone Q Pack 7 — Market Intent Confidence Calibration ===
python -m pytest tests/test_milestone_q_pack_7.py -v || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone Q Pack 7 validation completed successfully.
echo Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.
endlocal

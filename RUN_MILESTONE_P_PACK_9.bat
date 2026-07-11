@echo off
setlocal
python -m pytest tests/test_milestone_p_pack_9.py -v || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone P Pack 9 validation completed. Live execution remains disabled.

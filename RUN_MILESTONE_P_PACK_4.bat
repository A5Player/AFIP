@echo off
setlocal
pytest tests/test_milestone_p_pack_4.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone P Pack 4 validation complete. Live execution remains disabled.

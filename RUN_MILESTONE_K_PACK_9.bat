@echo off
pytest tests/test_milestone_k_pack_9.py -v || exit /b %errorlevel%
pytest || exit /b %errorlevel%
python tools/afip_local_quality_check.py || exit /b %errorlevel%
python -m afip.dashboard_ui || exit /b %errorlevel%
echo Milestone K Pack 9 validation PASS

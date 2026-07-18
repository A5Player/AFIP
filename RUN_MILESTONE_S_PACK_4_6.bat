@echo off
set PYTHONPATH=%CD%
python -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_6.py || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1

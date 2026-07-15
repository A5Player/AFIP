@echo off
cd /d %~dp0
python -m pytest tests\test_milestone_s_pack_5_1.py || exit /b 1
python -m pytest -q || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
echo AFIP Milestone S Pack 5.1 validation: PASS

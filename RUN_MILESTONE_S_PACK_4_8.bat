@echo off
setlocal
cd /d "%~dp0"
python -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_7.py tests\test_milestone_s_pack_4_8.py || exit /b 1
python -m pytest || exit /b 1
python tools\validate_financial_naming.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
endlocal

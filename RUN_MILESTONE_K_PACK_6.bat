@echo off
setlocal

echo === Milestone K Pack 6: Targeted Tests ===
python -m pytest tests/test_milestone_k_pack_6.py -v
if errorlevel 1 exit /b %errorlevel%

echo === Full Pytest ===
python -m pytest
if errorlevel 1 exit /b %errorlevel%

echo === AFIP Local Quality Check ===
python tools\afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%

echo === Dashboard Generation ===
python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%

echo Milestone K Pack 6 validation PASS
echo Git: git add .
echo Git: git commit -m "Milestone K Pack 6 Trailing Stop Intelligence"
echo Git: git push
endlocal

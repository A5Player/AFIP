@echo off
pytest tests/test_milestone_k_pack_2_smart_entry.py -v
if errorlevel 1 exit /b %errorlevel%
pytest
if errorlevel 1 exit /b %errorlevel%
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%
python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%
git add .
git commit -m "Milestone K Pack 2 Smart Entry Engine"
if errorlevel 1 exit /b %errorlevel%
git push

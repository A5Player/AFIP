@echo off
pytest tests/test_milestone_j_pack_7_entry_validation.py -v
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1
python -m afip.dashboard_ui
if errorlevel 1 exit /b 1
git add .
git commit -m "Milestone J Pack 7 Entry Validation Engine"
if errorlevel 1 exit /b 1
git push

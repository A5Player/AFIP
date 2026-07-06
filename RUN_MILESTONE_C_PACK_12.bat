@echo off
pytest tests/test_production_milestone_c_pack_12.py -v
if errorlevel 1 pause
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 pause
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 pause
if errorlevel 1 exit /b 1
git add .
git commit -m "Production Milestone C Pack 12"
git push
pause

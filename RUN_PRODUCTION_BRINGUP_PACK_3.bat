@echo off
pytest tests/test_production_bringup_pack_3.py -v
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python toolsfip_local_quality_check.py
if errorlevel 1 exit /b 1
python -m afip.dashboard_ui

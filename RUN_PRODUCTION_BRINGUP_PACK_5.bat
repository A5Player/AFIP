@echo off
pytest tests/test_production_bringup_pack_5.py -v
if errorlevel 1 exit /b 1

pytest
if errorlevel 1 exit /b 1

python tools\afip_local_quality_check.py
if errorlevel 1 exit /b 1

python -m afip.dashboard_ui
if errorlevel 1 exit /b 1

git add .
git commit -m "Production Bring-up Pack 5 Explainable Order Center"
if errorlevel 1 exit /b 1

git push
if errorlevel 1 exit /b 1

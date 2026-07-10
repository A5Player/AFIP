@echo off
pytest tests/test_milestone_i_pack_8_usd_index_intelligence.py -v
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1
python -m afip.dashboard_ui
if errorlevel 1 exit /b 1
git add .
git commit -m "Milestone I Pack 8 USD Index Intelligence"
git push

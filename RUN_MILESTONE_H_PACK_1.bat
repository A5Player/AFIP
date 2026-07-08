pytest tests/test_production_milestone_h_pack_1_dashboard_foundation.py -v
IF ERRORLEVEL 1 EXIT /B 1
pytest
IF ERRORLEVEL 1 EXIT /B 1
python tools/afip_local_quality_check.py
IF ERRORLEVEL 1 EXIT /B 1
git add .
git commit -m "Production Milestone H Pack 1 Dashboard Foundation"
git push

pytest tests/test_production_milestone_h_pack_2_configuration_center.py -v
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1
git add .
git commit -m "Production Milestone H Pack 2 Configuration Center"
git push

pytest tests/test_production_freeze_p5_walk_forward_simulation.py -v
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1
git add .
git commit -m "Production Freeze P5 Walk-Forward Historical Paper Simulation"
git push

pytest tests/test_production_freeze_p5_walk_forward_simulation.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Production Freeze P5 Walk-Forward Historical Paper Simulation"
git push

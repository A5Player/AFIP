pytest tests/test_production_bringup_pack_10.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Production Bring-up Pack 10 Production Certification"
git push

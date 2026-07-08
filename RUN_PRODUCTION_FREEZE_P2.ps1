pytest tests/test_production_freeze_p2_acceptance_test.py -v
if ($LASTEXITCODE -ne 0) { exit }

pytest
if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }

git add .
git commit -m "Production Freeze P2 Production Acceptance Test"
git push

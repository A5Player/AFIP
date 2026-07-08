pytest tests/test_production_freeze_p6_version1_freeze.py -v

if ($LASTEXITCODE -ne 0) { exit }

pytest

if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py

if ($LASTEXITCODE -ne 0) { exit }

git add .

git commit -m "Production Freeze P6 Version 1 Production Freeze"

git push

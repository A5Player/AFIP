pytest tests/test_production_freeze_p2_acceptance_test.py -v
if errorlevel 1 exit /b 1

pytest
if errorlevel 1 exit /b 1

python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1

git add .
git commit -m "Production Freeze P2 Production Acceptance Test"
git push

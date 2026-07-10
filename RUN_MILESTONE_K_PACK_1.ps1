pytest tests/test_milestone_k_pack_1_execution_intelligence_foundation.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git add .
git commit -m "Milestone K Pack 1 Execution Intelligence Foundation"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git push

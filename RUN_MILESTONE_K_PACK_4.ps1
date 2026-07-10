pytest tests/test_milestone_k_pack_4_dynamic_stop_loss.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git add .
git commit -m "Milestone K Pack 4 Dynamic Stop Loss Intelligence"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git push

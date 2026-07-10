pytest tests/test_milestone_j_pack_9_portfolio_decision.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git add .
git commit -m "Milestone J Pack 9 Portfolio Decision Engine"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git push

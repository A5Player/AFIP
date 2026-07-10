pytest tests/test_milestone_j_pack_10_decision_intelligence_certification.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git add .
git commit -m "Milestone J Pack 10 Decision Intelligence Certification"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git push

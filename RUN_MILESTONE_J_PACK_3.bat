@echo off
pytest tests/test_milestone_j_pack_3_conflict_resolver.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone J Pack 3 Conflict Resolver"
git push

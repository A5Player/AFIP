@echo off
pytest tests/test_milestone_i_pack_9_bond_yield_intelligence.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone I Pack 9 Bond Yield Intelligence"
git push

@echo off
pytest tests/test_milestone_j_pack_6_unit_allocation.py -v || exit /b 1
pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone J Pack 6 Unit Allocation Engine" || exit /b 1
git push || exit /b 1

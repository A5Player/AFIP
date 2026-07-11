@echo off
pytest tests/test_milestone_n_pack_4.py -v || exit /b 1
pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone N Pack 4 validation completed.
echo git add .
echo git commit -m "Milestone N Pack 4 Capital Allocation"
echo git push

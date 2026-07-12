@echo off
pytest tests/test_milestone_r_pack_7.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone R Pack 7 validation PASS

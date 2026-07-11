@echo off
pytest tests/test_milestone_o_pack_10.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone O Pack 10 validation completed. Milestone O is complete. Live execution remains disabled.

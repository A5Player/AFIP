@echo off
pytest tests/test_milestone_o_pack_6.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone O Pack 6 validation complete. Live execution remains disabled.

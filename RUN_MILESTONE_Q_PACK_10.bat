@echo off
pytest tests/test_milestone_q_pack_10.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
echo Milestone Q Pack 10 validation completed. Review results before git commit/push.

@echo off
pytest tests/test_milestone_i_pack_0_profile_customization.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone I Pack 0 Profile Customization Completion" || exit /b 1
git push

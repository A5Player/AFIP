@echo off
python -m pytest -q tests/test_milestone_s_pack_7_1_position_ceiling_semantics.py tests/test_milestone_s_pack_7_2_position_capacity_policy.py
exit /b %ERRORLEVEL%

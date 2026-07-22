# Phase U Pack 3.5 Validation

Targeted contract tests:

```powershell
python -m pytest tests/test_phase_u_pack_3_5_lot_authority.py tests/test_phase_u_pack_3_3_8_position_sizing_authority.py tests/test_milestone_s_pack_7_1_position_ceiling_semantics.py -q
```

Gateway and compatibility regression:

```powershell
python -m pytest tests/test_milestone_s_pack_4.py tests/test_milestone_s_pack_4_6.py tests/test_milestone_s_pack_4_7.py tests/test_milestone_s_pack_5_5.py tests/test_milestone_s_pack_7_2_position_capacity_policy.py tests/test_phase_u_pack_3_3_6_profile_execution_research_control.py -q
```

Then build dashboard once and run full regression. Do not claim production PASS until the user's Windows/VPS results and GitHub Actions are confirmed.

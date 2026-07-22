AFIP V1 Final Runtime Source Repair - Phase 2B

Files included:
- tools/afip_demo_execution_control.py
- tools/afip_profile_sequential_execution_router.py
- afip/final_integration/runtime.py

This package preserves the single runtime path.
It is prepared as the next source replacement package after Phase 2A.

Install:
Copy included files over the matching files under:
C:\AFIP\source

Validate:
python -m pytest -q

Verify:
git diff --stat
git status

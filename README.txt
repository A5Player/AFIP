AFIP V1 FINAL CAPITAL AUTHORITY FINAL ALIGNMENT PATCH

Purpose:
Minimal capital contract alignment.

Changes:
- Keep CAPITAL_TIER_TABLE as execution allocation contract.
- Restore legacy compatibility flag.
- Keep P4 as experimental execution profile with conservative 0.01 lot.

Files:
- config/four_profile_demo.json
- afip/position_capacity_formula.py

Install:
Copy files over matching paths under C:\AFIP\source

Validate:
cd C:\AFIP\source
python -m pytest -q

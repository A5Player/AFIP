AFIP V1 Final Capital Authority Source Rebuild Patch

Purpose:
Restore Capital Authority source-of-truth ladder compatibility.

Modified:
- config/four_profile_demo.json
- afip/position_capacity_formula.py
- afip/demo_execution_gateway/runtime.py

Install:
Copy files from this package over the matching files in C:\AFIP\source

Validate:
cd C:\AFIP\source
.\.venv\Scripts\Activate.ps1
python -m pytest -q

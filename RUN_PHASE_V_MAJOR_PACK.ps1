$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase V Major Pack - Historical-to-Live Autonomous Research Runtime"
Write-Host "Safety: validation does not arm or start live execution."
python -m pytest tests/test_phase_v_major_pack.py -q
python -m tools.afip_phase_v_major run-once
Write-Host "Phase V one-cycle validation complete. Review runtime/research/phase_v_major_status.json."

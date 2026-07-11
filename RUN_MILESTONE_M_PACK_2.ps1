$ErrorActionPreference = "Stop"

Write-Host "=== Milestone M Pack 2 — Targeted Test ==="
python -m pytest tests/test_milestone_m_pack_2.py -v

Write-Host "=== Full Pytest ==="
python -m pytest

Write-Host "=== AFIP Local Quality Check ==="
python tools/afip_local_quality_check.py

Write-Host "=== Dashboard Generation ==="
python -m afip.dashboard_ui

Write-Host "Milestone M Pack 2 validation completed. Live execution remains disabled."

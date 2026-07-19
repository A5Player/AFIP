$ErrorActionPreference = "Continue"
Write-Host "=== AFIP Milestone T Pack 14 ==="
Write-Host "Unattended Continuity, Restart Reconciliation and Recovery Supervision"
python -m pytest tests/test_milestone_t_pack_14_unattended_continuity.py -q
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 14 validation completed."

$ErrorActionPreference = "Stop"

Write-Host "=== Milestone K Pack 6: Targeted Tests ==="
python -m pytest tests/test_milestone_k_pack_6.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Full Pytest ==="
python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== AFIP Local Quality Check ==="
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Dashboard Generation ==="
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Milestone K Pack 6 validation PASS"
Write-Host 'Git: git add .'
Write-Host 'Git: git commit -m "Milestone K Pack 6 Trailing Stop Intelligence"'
Write-Host 'Git: git push'

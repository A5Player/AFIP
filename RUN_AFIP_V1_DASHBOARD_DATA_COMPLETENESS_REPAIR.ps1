param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "AFIP V1 Dashboard Data Completeness Repair"
python -m pytest `
  tests/test_afip_v1_dashboard_data_completeness_repair.py `
  tests/test_afip_v1_control_center_pack_1.py `
  tests/test_production_milestone_h_pack_8.py `
  tests/test_afip_final_account_routing_realtime_ranking_fix.py `
  -q

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Focused dashboard certification: PASS"
Write-Host "Start monitor separately with: python -m tools.afip_dashboard_monitor"

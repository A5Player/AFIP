$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.3.5 - Dashboard Coverage, Progress, Freshness & Research Status Integration"
Write-Host "Safety: stop active AFIP research writers before validation."
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
try { & (Join-Path $Root 'APPLY_PHASE_U_PACK_3_3_5_DOC_UPDATES.ps1') }
catch { throw "Documentation update failed: $($_.Exception.Message)" }
python -m pytest -q tests/test_phase_u_pack_3_3_5_dashboard_timeframe_status.py tests/test_phase_u_pack_3_three_dashboards.py tests/test_phase_u_pack_3_1_2_compact_dashboards_1_and_3.py
if ($LASTEXITCODE -ne 0) { throw "Phase U Pack 3.3.5 validation failed." }
Write-Host "PASS - universal timeframe dashboard coverage, replay, freshness, gap, integrity, and research status validated."
Write-Host "Live execution policy was not changed."

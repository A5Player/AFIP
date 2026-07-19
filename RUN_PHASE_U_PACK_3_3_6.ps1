$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.3.6 - Research Consumer Integration & Operational Profile Execution Control"
Write-Host "Safety: stop active AFIP execution and research writers before applying profile control changes."
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
try { & (Join-Path $Root 'APPLY_PHASE_U_PACK_3_3_6_DOC_UPDATES.ps1') }
catch { throw "Documentation update failed: $($_.Exception.Message)" }
python -m pytest -q tests/test_phase_u_pack_3_3_6_profile_execution_research_control.py tests/test_phase_u_pack_3_3_5_dashboard_timeframe_status.py tests/test_phase_u_pack_3_3_1_timeframe_registry.py
if ($LASTEXITCODE -ne 0) { throw "Phase U Pack 3.3.6 validation failed." }
Write-Host "PASS - research consumer access and P1/P4 execution-only profile control validated."
Write-Host "P2 and P3 execution are disabled; configuration, historical data, and research participation are preserved."
Write-Host "Live execution policy was not changed."

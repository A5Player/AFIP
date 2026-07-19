$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.3.3 - M30 Chronological Replay & Coverage Evidence"
Write-Host "Safety: stop active AFIP research writers before validation."
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
try { & (Join-Path $Root 'APPLY_PHASE_U_PACK_3_3_3_DOC_UPDATES.ps1') }
catch { throw "Documentation update failed: $($_.Exception.Message)" }
python -m pytest -q tests/test_phase_u_pack_3_3_3_m30_replay_coverage.py tests/test_phase_u_pack_3_3_1_timeframe_registry.py tests/test_phase_u_pack_3_3_2_m30_historical_data_lake.py tests/test_phase_u_pack_3_2_2_stale_replay_checkpoint_recovery.py
if ($LASTEXITCODE -ne 0) { throw "Phase U Pack 3.3.3 validation failed." }
Write-Host "PASS - M30 replay and exact-window coverage evidence validated."
Write-Host "Live execution policy was not changed."

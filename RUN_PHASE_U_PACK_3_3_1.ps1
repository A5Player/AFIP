$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "AFIP Phase U Pack 3.3.1 - Universal Timeframe Registry"
Write-Host "Safety: stop active AFIP research writers before validation."

try {
    & ".\APPLY_PHASE_U_PACK_3_3_1_DOC_UPDATES.ps1"
}
catch {
    throw "Documentation update failed: $($_.Exception.Message)"
}

python -m pytest tests/test_phase_u_pack_3_3_1_timeframe_registry.py tests/test_phase_u_pack_3_2_2_stale_replay_checkpoint_recovery.py -q
if ($LASTEXITCODE -ne 0) {
    throw "Pack 3.3.1 tests failed with exit code $LASTEXITCODE."
}

Write-Host "PASS - universal timeframe registry and M30 foundation validated."
Write-Host "Live execution policy was not changed."

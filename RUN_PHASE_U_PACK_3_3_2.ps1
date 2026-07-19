$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "AFIP Phase U Pack 3.3.2 - M30 Historical Collection & Data Lake Integration"
Write-Host "Safety: stop active AFIP research writers before validation."
try { & "$PSScriptRoot\APPLY_PHASE_U_PACK_3_3_2_DOC_UPDATES.ps1" } catch { throw "Documentation update failed: $($_.Exception.Message)" }
python -m pytest tests/test_phase_u_pack_3_3_1_timeframe_registry.py tests/test_phase_u_pack_3_3_2_m30_historical_data_lake.py -q
if ($LASTEXITCODE -ne 0) { throw "Pack 3.3.2 validation failed." }
Write-Host "PASS - M30 historical collection and append-only data lake integration validated."
Write-Host "Live execution policy was not changed."

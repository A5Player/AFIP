param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location $ProjectRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "AFIP virtual environment not found: $ProjectRoot\.venv"
}

& ".\.venv\Scripts\python.exe" -m pytest `
    tests\test_afip_v1_mt5_research_collection_repair.py `
    tests\test_phase_u_pack_3_2_automatic_research_runtime.py `
    tests\test_phase_u_pack_3_3_4_m30_quality_backfill.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "AFIP V1 MT5 Research Collection Repair validation failed."
}

Write-Host "AFIP V1 MT5 Research Collection Repair validation: PASS"

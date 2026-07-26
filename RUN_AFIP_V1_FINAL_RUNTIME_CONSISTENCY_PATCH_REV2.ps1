param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}

python -m pytest `
    tests\test_afip_v1_final_runtime_consistency_patch.py `
    tests\test_afip_v1_final_integration.py `
    tests\test_afip_v1_final_consolidation.py `
    -q

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP V1 Final Runtime Consistency REV2 focused certification: PASS" -ForegroundColor Green

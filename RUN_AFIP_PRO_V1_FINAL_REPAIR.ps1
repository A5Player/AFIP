param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python -m pytest -q `
    tests\test_afip_pro_final_runtime_truth_repair.py `
    tests\test_afip_pro_production_dashboard_polish.py `
    tests\test_afip_pro_final_financial_dashboard_authority.py `
    tests\test_afip_v1_dashboard_passive_truth_completion.py `
    tests\test_afip_v1_dashboard_operations_health_semantics.py `
    tests\test_afip_v1_dashboard_health_market_no_event_semantics.py `
    tests\test_afip_v1_order_evidence_truth_separation.py

if ($LASTEXITCODE -ne 0) {
    throw "Focused regression failed with exit code $LASTEXITCODE"
}

& $Python -m tools.afip_dashboard_monitor --once
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Dashboard monitor --once was not supported or returned non-zero. Run START_AFIP.ps1 normally to refresh the dashboard."
}

Write-Host ""
Write-Host "AFIP Pro V1 Final Repair validation: PASS" -ForegroundColor Green

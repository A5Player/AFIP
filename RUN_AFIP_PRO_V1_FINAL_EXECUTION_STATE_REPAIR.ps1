param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
Push-Location $ProjectRoot
try {
    $Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        $Python = "python"
    }

    & $Python -m pytest `
        tests\test_afip_pro_v1_final_execution_state_repair.py `
        tests\test_afip_pro_live_mt5_snapshot_authority.py `
        tests\test_afip_pro_production_dashboard_polish.py `
        tests\test_afip_pro_final_financial_dashboard_authority.py `
        tests\test_afip_v1_dashboard_runtime_state_machine.py `
        tests\test_afip_v1_dashboard_data_contract_phase_1.py `
        -q

    if ($LASTEXITCODE -ne 0) {
        throw "Focused regression failed with exit code $LASTEXITCODE"
    }

    & $Python -m afip.dashboard_ui
    if ($LASTEXITCODE -ne 0) {
        throw "Dashboard rebuild failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "AFIP Pro V1 Final Execution State Repair validation: PASS"
}
finally {
    Pop-Location
}

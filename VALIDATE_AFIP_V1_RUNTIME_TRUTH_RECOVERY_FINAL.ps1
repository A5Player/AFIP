param(
    [Parameter(Mandatory=$false)][string]$ProjectRoot = "C:\AFIP",
    [switch]$FullRegression
)
$ErrorActionPreference = "Stop"
$Required = @(
    "afip\runtime_truth.py",
    "afip\dashboard_operations_health.py",
    "afip\dashboard_data_contract.py",
    "afip\four_profile_operations\mt5_connection.py",
    "afip\dashboard_ui\split_runtime.py",
    "tests\test_afip_v1_runtime_truth_recovery_final.py"
)
foreach ($Relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $Relative) -PathType Leaf)) { throw "Installed file missing: $Relative" }
}
Push-Location $ProjectRoot
try {
    python -m py_compile `
      afip\runtime_truth.py `
      afip\dashboard_operations_health.py `
      afip\dashboard_data_contract.py `
      afip\four_profile_operations\mt5_connection.py `
      afip\dashboard_ui\split_runtime.py `
      tests\test_afip_v1_runtime_truth_recovery_final.py
    if ($LASTEXITCODE -ne 0) { throw "Changed-file compilation failed" }
    python -m pytest -q `
      tests\test_afip_v1_runtime_truth_recovery_final.py `
      tests\test_afip_v1_single_runtime_truth_refactor.py `
      tests\test_afip_v1_runtime_truth_passive_monitoring_final.py `
      tests\test_afip_v1_dashboard_passive_truth_completion.py `
      tests\test_afip_v1_passive_mt5_monitoring.py `
      tests\test_afip_v1_dashboard_operations_health_semantics.py
    if ($LASTEXITCODE -ne 0) { throw "Focused Runtime Truth regression failed" }
    if ($FullRegression) {
        python -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw "Full regression failed" }
    }
    python -m afip.dashboard_ui
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed" }
    Write-Host "VALIDATION PASS" -ForegroundColor Green
    Write-Host "No active MT5 diagnostic was run."
}
finally { Pop-Location }

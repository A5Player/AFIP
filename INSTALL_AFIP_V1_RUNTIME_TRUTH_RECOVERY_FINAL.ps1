param(
    [Parameter(Mandatory=$false)][string]$ProjectRoot = "C:\AFIP"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Files = @(
    "afip\runtime_truth.py",
    "afip\dashboard_operations_health.py",
    "afip\dashboard_data_contract.py",
    "afip\four_profile_operations\mt5_connection.py",
    "afip\dashboard_ui\split_runtime.py",
    "tests\test_afip_v1_runtime_truth_recovery_final.py"
)
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "ProjectRoot not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "afip") -PathType Container)) { throw "Not an AFIP project root: $ProjectRoot" }
foreach ($Relative in $Files) {
    $Source = Join-Path $PackRoot $Relative
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Pack file missing: $Relative" }
}
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot ("runtime\backups\runtime_truth_recovery_final_" + $Stamp)
foreach ($Relative in $Files) {
    $Source = Join-Path $PackRoot $Relative
    $Target = Join-Path $ProjectRoot $Relative
    $TargetDir = Split-Path -Parent $Target
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    if (Test-Path -LiteralPath $Target -PathType Leaf) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
        Copy-Item -LiteralPath $Target -Destination $Backup -Force
    }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
    Write-Host "Installed: $Relative"
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
    python -m afip.dashboard_ui
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed" }
    Write-Host "AFIP V1 Runtime Truth Recovery Final: PASS" -ForegroundColor Green
    Write-Host "Backup: $BackupRoot"
    Write-Host "Active MT5 diagnostic was NOT run."
}
finally { Pop-Location }

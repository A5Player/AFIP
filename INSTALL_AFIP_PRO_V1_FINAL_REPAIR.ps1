param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "runtime\backups\afip_pro_v1_final_repair_$Timestamp"

$Files = @(
    "afip\live_mt5_snapshot_authority.py",
    "afip\dashboard_data_contract.py",
    "afip\dashboard_state_machine.py",
    "afip\dashboard_ui\split_runtime.py",
    "tests\test_afip_pro_final_runtime_truth_repair.py"
)

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

foreach ($Relative in $Files) {
    $Source = Join-Path $PackRoot $Relative
    $Target = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path $Source)) {
        throw "Patch source missing: $Source"
    }
    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
        Copy-Item -Force $Target $Backup
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    Copy-Item -Force $Source $Target
    Write-Host "Installed: $Relative"
}

$RunnerSource = Join-Path $PackRoot "RUN_AFIP_PRO_V1_FINAL_REPAIR.ps1"
$RunnerTarget = Join-Path $ProjectRoot "RUN_AFIP_PRO_V1_FINAL_REPAIR.ps1"
Copy-Item -Force $RunnerSource $RunnerTarget

Write-Host ""
Write-Host "AFIP Pro V1 Final Repair installed successfully." -ForegroundColor Green
Write-Host "Backup: $BackupRoot"
Write-Host "Run validation:"
Write-Host "  .\RUN_AFIP_PRO_V1_FINAL_REPAIR.ps1 -ProjectRoot $ProjectRoot"

param(
    [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupRoot = Join-Path $ProjectRoot ("runtime\patch_backups\maximum_lot_authority_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

$Files = @(
    "config\four_profile_demo.json",
    "afip\position_capacity_formula.py",
    "tests\test_afip_final_capital_tier_authority.py",
    "tests\test_afip_account_isolation_capital_safety.py"
)

foreach ($RelativePath in $Files) {
    $Source = Join-Path $PatchRoot $RelativePath
    $Target = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path $Source)) { throw "Patch source missing: $Source" }

    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $RelativePath
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
        Copy-Item -Force $Target $Backup
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    Copy-Item -Force $Source $Target
    Write-Host "Installed: $RelativePath"
}

Write-Host ""
Write-Host "Maximum Lot Size + Maximum Lot Unit authority patch installed."
Write-Host "Backup: $BackupRoot"
Write-Host "No MT5 terminal was started and execution mode was not changed."

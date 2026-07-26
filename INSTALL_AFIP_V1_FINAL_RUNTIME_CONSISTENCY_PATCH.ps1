param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "runtime\patch_backups\final_runtime_consistency_$Timestamp"

$Files = @(
    "afip\final_integration\runtime.py",
    "afip\automatic_research_runtime\runtime.py",
    "tests\test_afip_v1_final_runtime_consistency_patch.py"
)

Write-Host "AFIP V1 Final Runtime Consistency Patch" -ForegroundColor Cyan
Write-Host "ProjectRoot: $ProjectRoot"

foreach ($Relative in $Files) {
    $Source = Join-Path $PatchRoot $Relative
    $Target = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path $Source)) { throw "Patch source missing: $Source" }

    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
        Copy-Item -Force $Target $Backup
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    Copy-Item -Force $Source $Target
    Write-Host "Installed: $Relative" -ForegroundColor Green
}

Write-Host "Backup: $BackupRoot" -ForegroundColor Yellow
Write-Host "Patch installation complete." -ForegroundColor Green

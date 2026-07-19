$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path (Join-Path $Root "afip"))) {
    throw "AFIP repository not found. Extract this ZIP directly into C:\AFIP, then run the installer from C:\AFIP."
}
$PatchRoot = Join-Path $Root "PATCH"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Root "backup\phase_u_pack_3_4_8_command_center_$Timestamp"
$Targets = @(
    "afip\dashboard_ui\home.py",
    "tests\test_phase_u_pack_3_4_8_command_center.py"
)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
foreach ($Relative in $Targets) {
    $Source = Join-Path $PatchRoot $Relative
    if (-not (Test-Path $Source)) { throw "Missing patch file: $Source" }
    $Destination = Join-Path $Root $Relative
    if (Test-Path $Destination) {
        $BackupFile = Join-Path $Backup $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupFile) | Out-Null
        Copy-Item $Destination $BackupFile -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Copy-Item $Source $Destination -Force
}
Write-Host "AFIP Phase U Pack 3.4.8 installed." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Next: .\RUN_PHASE_U_PACK_3_4_8_COMMAND_CENTER.ps1"

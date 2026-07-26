param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
$PatchRoot = Join-Path $PSScriptRoot "payload"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "runtime\patch_backups\final_lightweight_dashboard_$Stamp"
$Files = @(
  "afip\dashboard_ui\dashboard_authority.py",
  "afip\final_integration\runtime.py",
  "tools\afip_dashboard_monitor.py",
  "tests\test_afip_v1_final_lightweight_realtime_dashboard.py"
)
foreach ($Relative in $Files) {
  $Source = Join-Path $PatchRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  if (!(Test-Path $Source)) { throw "Missing patch file: $Source" }
  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path $Backup) | Out-Null
    Copy-Item -Force $Target $Backup
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}
Write-Host "Backup: $BackupRoot"
Write-Host "AFIP V1 Final Lightweight Realtime Dashboard installed."

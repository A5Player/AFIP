param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $ProjectRoot "runtime\backups\runtime_execution_repair_pack_1\$Stamp"
$Files = @(
  "afip\demo_execution_gateway\runtime.py",
  "tools\afip_profile_execution_once.py",
  "tests\test_afip_v1_runtime_execution_repair_pack_1.py"
)
foreach ($Relative in $Files) {
  $Source = Join-Path $PackRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  if (Test-Path $Target) {
    $BackupTarget = Join-Path $Backup $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupTarget) | Out-Null
    Copy-Item -Force $Target $BackupTarget
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}
Write-Host "Backup: $Backup"
Write-Host "Runtime execution repair Pack 1 installed. Dashboard files were not changed."

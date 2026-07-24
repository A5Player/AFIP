param(
  [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$BackupRoot = Join-Path $ProjectRoot "runtime\backups\runtime_certification_repair_pack_2\$Stamp"

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
  throw "ProjectRoot is not the AFIP Git repository: $ProjectRoot"
}

$CopyFiles = @(
  "afip\demo_execution_gateway\runtime.py",
  "tools\afip_profile_sequential_execution_router.py",
  "tools\afip_demo_execution_control.py",
  "tests\test_afip_v1_runtime_certification_repair_pack_2.py"
)

$RemoveFiles = @(
  "tools\afip_profile_execution_worker.py",
  "tests\test_afip_v1_one_process_per_profile_repair.py",
  "RUN_AFIP_V1_ONE_PROCESS_PER_PROFILE_REPAIR.ps1"
)

foreach ($Relative in $CopyFiles + $RemoveFiles) {
  $Target = Join-Path $ProjectRoot $Relative
  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
    Copy-Item -Force $Target $Backup
    Write-Host "Backed up: $Relative"
  }
}

foreach ($Relative in $CopyFiles) {
  $Source = Join-Path $PackRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}

foreach ($Relative in $RemoveFiles) {
  $Target = Join-Path $ProjectRoot $Relative
  if (Test-Path $Target) {
    Remove-Item -Force $Target
    Write-Host "Removed obsolete duplicate: $Relative"
  }
}

Write-Host "AFIP V1 Runtime Certification Repair Pack 2 installed."
Write-Host "Backup: $BackupRoot"

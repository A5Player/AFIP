param(
  [string]$ProjectRoot = "C:\AFIP\source"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot = Join-Path $PackRoot "patch_payload"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_CERTIFICATION_REPAIR_PACK_3_$Stamp"
$Files = @(
  "afip\lot_authority\runtime.py",
  "config\four_profile_demo.json",
  "tests\test_afip_v1_final_maximum_lot_size_unit_policy.py"
)
foreach ($Relative in $Files) {
  $Source = Join-Path $PayloadRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  if (-not (Test-Path $Source)) { throw "Missing patch payload: $Source" }
  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
    Copy-Item -Force $Target $Backup
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}
Write-Host "Backup: $BackupRoot"
Write-Host "AFIP V1 Final Certification Repair Pack 3 installed."

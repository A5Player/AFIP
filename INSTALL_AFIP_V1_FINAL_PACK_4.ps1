param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $PackRoot "payload"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_PACK_4_$Stamp"
$Files = @(
  "afip\demo_execution_gateway\runtime.py",
  "afip\protection\sl_tp_planner.py",
  "tools\afip_demo_execution_control.py",
  "tools\afip_v1_pack_4_demo_execution_certification.py",
  "tests\test_phase25_position_protection.py",
  "tests\test_afip_v1_pack_4_production_certification_repair.py"
)
if (!(Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
foreach ($Rel in $Files) {
  $Source = Join-Path $Payload $Rel
  $Target = Join-Path $ProjectRoot $Rel
  if (!(Test-Path $Source)) { throw "Payload missing: $Rel" }
  if (Test-Path $Target) {
    $BackupTarget = Join-Path $Backup $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupTarget) | Out-Null
    Copy-Item -Force $Target $BackupTarget
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Rel"
}
Set-Content -Path (Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_PACK_4_LAST_BACKUP.txt") -Value $Backup -Encoding UTF8
Write-Host "Backup: $Backup"
Write-Host "Pack 4 installation complete."

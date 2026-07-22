param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$files = @(
  "afip\lot_authority\runtime.py",
  "afip\demo_execution_gateway\runtime.py",
  "afip\production_certification\runtime.py",
  "afip\production_certification\incremental_financial_naming.py",
  "tools\afip_demo_execution_control.py",
  "config\four_profile_demo.json"
)
if (-not (Test-Path $ProjectRoot)) { throw "ProjectRoot not found: $ProjectRoot" }
$backup = Join-Path $ProjectRoot ("backup\AFIP_V1_FINAL_CERTIFICATION_REPAIR_PACK_2_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
foreach ($relative in $files) {
  $source = Join-Path $PackRoot $relative
  $target = Join-Path $ProjectRoot $relative
  if (-not (Test-Path $source)) { throw "Pack file missing: $source" }
  if (Test-Path $target) {
    $backupTarget = Join-Path $backup $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupTarget) | Out-Null
    Copy-Item -Force $target $backupTarget
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  Copy-Item -Force $source $target
  Write-Host "Installed: $relative"
}
Write-Host "Backup: $backup"
Write-Host "AFIP V1 Final Certification Repair Pack 2 installed."

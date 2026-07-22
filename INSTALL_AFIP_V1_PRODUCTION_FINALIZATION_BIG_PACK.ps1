param([Parameter(Mandatory=$false)][string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot = Join-Path $PackRoot "payload"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
if (-not (Test-Path $ProjectRoot)) { throw "ProjectRoot not found: $ProjectRoot" }
if (-not (Test-Path (Join-Path $ProjectRoot "afip"))) { throw "AFIP source root not detected: $ProjectRoot" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "runtime\installation_backups\AFIP_V1_PRODUCTION_FINALIZATION_BIG_PACK_$Stamp"
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$Files = Get-Content (Join-Path $PayloadRoot "FILE_LIST_AFIP_V1_PRODUCTION_FINALIZATION_BIG_PACK.txt") | Where-Object { $_.Trim() }
foreach ($Relative in $Files) {
  $Source = Join-Path $PayloadRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  if (-not (Test-Path $Source)) { throw "Pack file missing: $Relative" }
  $SourceFull = [System.IO.Path]::GetFullPath($Source)
  $TargetFull = [System.IO.Path]::GetFullPath($Target)
  if ($SourceFull -eq $TargetFull) { Write-Host "Already in project: $Relative"; continue }
  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
    Copy-Item -Force $Target $Backup
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}
$AppendSource = Join-Path $ProjectRoot "AFIP_PROJECT_DATABASE_V1_PRODUCTION_FINALIZATION_BIG_PACK_APPEND.md"
$Database = Join-Path $ProjectRoot "AFIP_PROJECT_DATABASE.md"
if ((Test-Path $AppendSource) -and (Test-Path $Database)) {
  $Marker = "## AFIP V1 Production Finalization Big Pack"
  $Current = Get-Content $Database -Raw
  if ($Current -notlike "*$Marker*") { Add-Content -Path $Database -Value (Get-Content $AppendSource -Raw) -Encoding UTF8 }
}
Write-Host ""
Write-Host "AFIP V1 Production Finalization Big Pack installed."
Write-Host "Backup: $BackupRoot"
Write-Host "Run: .\RUN_AFIP_V1_PRODUCTION_FINALIZATION_BIG_PACK.ps1"

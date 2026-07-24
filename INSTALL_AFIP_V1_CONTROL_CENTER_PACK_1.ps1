param([string]$ProjectRoot = 'C:\AFIP\source')
$ErrorActionPreference = 'Stop'
$PackRoot = $PSScriptRoot
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$PackRoot = [System.IO.Path]::GetFullPath($PackRoot)
if (-not (Test-Path $ProjectRoot -PathType Container)) { throw "ProjectRoot not found: $ProjectRoot" }
if (-not (Test-Path (Join-Path $ProjectRoot 'afip') -PathType Container)) { throw "AFIP source not found under: $ProjectRoot" }
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$BackupRoot = Join-Path $ProjectRoot "runtime\backups\control_center_pack_1\$Stamp"
$Files = @(
 'afip\control_center_runtime.py',
 'afip\dashboard_ui\control_center.py',
 'afip\dashboard_ui\dashboard_authority.py',
 'afip\dashboard_ui\home.py',
 'afip\dashboard_ui\__main__.py',
 'tests\test_afip_v1_control_center_pack_1.py'
)
foreach ($Relative in $Files) {
  $Source = [System.IO.Path]::GetFullPath((Join-Path $PackRoot $Relative))
  $Target = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Relative))
  if (-not (Test-Path $Source -PathType Leaf)) { throw "Pack source missing: $Source" }
  if ($Source -eq $Target) { Write-Host "Skipped self-copy: $Relative"; continue }
  $TargetDir = Split-Path -Parent $Target
  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  if (Test-Path $Target -PathType Leaf) {
    $Backup = Join-Path $BackupRoot $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
    Copy-Item -LiteralPath $Target -Destination $Backup -Force
  }
  Copy-Item -LiteralPath $Source -Destination $Target -Force
  Write-Host "Installed: $Relative"
}
Write-Host "Backup: $BackupRoot"
Write-Host 'Installation complete. Execution authority was not changed.'

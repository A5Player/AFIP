param([Parameter(Mandatory=$true)][string]$ProjectRoot)

$ErrorActionPreference = 'Stop'
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupRoot = Join-Path $ProjectRoot "runtime\installation_backups\v1_certification_performance_hotfix_$Timestamp"

$Files = @(
  'afip/production_certification/__init__.py',
  'afip/production_certification/io.py',
  'afip/production_certification/fingerprint.py',
  'afip/production_certification/incremental_financial_naming.py',
  'afip/production_certification/runtime.py',
  'tools/validate_financial_naming.py',
  'tests/test_afip_v1_certification_performance_hotfix.py',
  'README_AFIP_V1_CERTIFICATION_PERFORMANCE_HOTFIX_TH.md'
)

foreach ($Relative in $Files) {
  $Source = Join-Path $SourceRoot ($Relative -replace '/', '\')
  $Target = Join-Path $ProjectRoot ($Relative -replace '/', '\')
  if (-not (Test-Path $Source)) { throw "Missing pack file: $Relative" }

  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot ($Relative -replace '/', '\')
    New-Item -ItemType Directory -Force -Path (Split-Path $Backup -Parent) | Out-Null
    Copy-Item -Force $Target $Backup
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Target -Parent) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}

Write-Host "Backup: $BackupRoot"
Write-Host 'AFIP V1 Certification Performance Hotfix installed.'

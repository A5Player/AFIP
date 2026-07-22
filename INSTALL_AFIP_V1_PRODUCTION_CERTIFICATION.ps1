param([Parameter(Mandatory=$true)][string]$ProjectRoot)

$ErrorActionPreference = 'Stop'
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupRoot = Join-Path $ProjectRoot "runtime\installation_backups\v1_production_certification_$Timestamp"

$Files = @(
  'afip/production_certification/__init__.py',
  'afip/production_certification/io.py',
  'afip/production_certification/fingerprint.py',
  'afip/production_certification/incremental_financial_naming.py',
  'afip/production_certification/runtime.py',
  'tools/afip_production_certification.py',
  'tools/validate_financial_naming.py',
  'tests/test_afip_v1_production_certification.py',
  'RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1',
  'RUN_AFIP_V1_PRODUCTION_CERTIFICATION.bat',
  'README_AFIP_V1_PRODUCTION_CERTIFICATION.md',
  'README_AFIP_V1_PRODUCTION_CERTIFICATION_TH.md',
  'VALIDATION_AFIP_V1_PRODUCTION_CERTIFICATION.md',
  'HANDOFF_AFIP_V1_PRODUCTION_CERTIFICATION.md',
  'AFIP_PROJECT_DATABASE_V1_PRODUCTION_CERTIFICATION_APPEND.md',
  'FILE_LIST_AFIP_V1_PRODUCTION_CERTIFICATION.txt'
)

$ExistingValidator = Join-Path $ProjectRoot 'tools\validate_financial_naming.py'
$LegacyValidator = Join-Path $ProjectRoot 'tools\validate_financial_naming_legacy.py'

if ((Test-Path $ExistingValidator) -and -not (Test-Path $LegacyValidator)) {
  New-Item -ItemType Directory -Force -Path (Split-Path $LegacyValidator -Parent) | Out-Null
  Copy-Item -Force $ExistingValidator $LegacyValidator
  Write-Host 'Preserved legacy validator: tools/validate_financial_naming_legacy.py'
}

foreach ($Relative in $Files) {
  $Source = Join-Path $SourceRoot ($Relative -replace '/', '\')
  if (-not (Test-Path $Source)) { throw "Pack file missing: $Relative" }

  $Target = Join-Path $ProjectRoot ($Relative -replace '/', '\')
  $SourceFull = [IO.Path]::GetFullPath($Source)
  $TargetFull = [IO.Path]::GetFullPath($Target)

  if ($SourceFull -ieq $TargetFull) {
    Write-Host "Skipped self-copy: $Relative"
    continue
  }

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
Write-Host 'AFIP V1 Production Certification installed as Patch Only.'

param(
  [switch]$FullRegression,
  [switch]$ForceFinancialNaming,
  [switch]$Mt5Check,
  [string]$ProjectRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }

$Arguments = @(
  '-m', 'tools.afip_production_certification',
  '--root', $ProjectRoot,
  'certify'
)

if ($FullRegression) { $Arguments += '--full-regression' }
if ($ForceFinancialNaming) { $Arguments += '--force-financial-naming' }
if ($Mt5Check) { $Arguments += '--mt5-check' }

& $Python @Arguments
if ($LASTEXITCODE -ne 0) {
  throw 'AFIP V1 Production Certification FAILED. See runtime\certification\production_certification.json'
}

Write-Host ''
Write-Host 'AFIP V1 PRODUCTION CERTIFICATION PASS'
Write-Host ('Report: ' + (Join-Path $ProjectRoot 'runtime\certification\production_certification.json'))

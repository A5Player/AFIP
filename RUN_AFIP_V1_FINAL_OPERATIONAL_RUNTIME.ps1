param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Test")]
  [string]$Action = "Start",
  [int]$IntervalSeconds = 60,
  [string]$ProjectRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }

Write-Host "AFIP V1 Runtime Core Control (compatibility wrapper)" -ForegroundColor Cyan
Write-Host "Lifecycle Authority: FINAL_INTEGRATION_RUNTIME" -ForegroundColor Yellow
Write-Host "MT5 Policy: MANUAL START ONLY / AFIP AUTO-LAUNCH DISABLED" -ForegroundColor Yellow

switch ($Action) {
  "Test" {
    & $Python -m pytest tests\test_afip_single_runtime_authority_repair_pack_2.py tests\test_afip_v1_final_integration.py tests\test_final_integration_regression_fix.py -q
  }
  "Start" {
    & (Join-Path $ProjectRoot 'START_AFIP.ps1') -ProjectRoot $ProjectRoot
    if ($LASTEXITCODE -eq 0) { & (Join-Path $ProjectRoot 'STATUS_AFIP.ps1') -ProjectRoot $ProjectRoot }
  }
  "Stop" {
    & (Join-Path $ProjectRoot 'STOP_AFIP.ps1') -ProjectRoot $ProjectRoot
  }
  "Restart" {
    & (Join-Path $ProjectRoot 'STOP_AFIP.ps1') -ProjectRoot $ProjectRoot
    if ($LASTEXITCODE -eq 0) {
      Start-Sleep -Seconds 2
      & (Join-Path $ProjectRoot 'START_AFIP.ps1') -ProjectRoot $ProjectRoot
    }
    if ($LASTEXITCODE -eq 0) {
      Start-Sleep -Seconds 2
      & (Join-Path $ProjectRoot 'STATUS_AFIP.ps1') -ProjectRoot $ProjectRoot
    }
  }
  "Status" {
    & (Join-Path $ProjectRoot 'STATUS_AFIP.ps1') -ProjectRoot $ProjectRoot
  }
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Test")]
  [string]$Action = "Start",
  [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Missing .venv Python: $Python" }

Write-Host "AFIP V1 Runtime Core Control" -ForegroundColor Cyan
Write-Host "Lifecycle Authority: OPERATIONAL_SUPERVISOR" -ForegroundColor Yellow
Write-Host "MT5 Policy: MANUAL START ONLY / AFIP AUTO-LAUNCH DISABLED" -ForegroundColor Yellow

switch ($Action) {
  "Test" {
    & $Python -m pytest tests\test_afip_v1_operational_runtime_repair.py tests\test_afip_v1_runtime_core_stabilization.py -q
  }
  "Start" {
    & $Python -m tools.afip_operational_runtime start --interval-seconds $IntervalSeconds
    Start-Sleep -Seconds 3
    & $Python -m tools.afip_operational_runtime status
  }
  "Stop" {
    & $Python -m tools.afip_operational_runtime stop --interval-seconds $IntervalSeconds
  }
  "Restart" {
    & $Python -m tools.afip_operational_runtime restart --interval-seconds $IntervalSeconds
    Start-Sleep -Seconds 3
    & $Python -m tools.afip_operational_runtime status
  }
  "Status" {
    & $Python -m tools.afip_operational_runtime status --interval-seconds $IntervalSeconds
  }
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

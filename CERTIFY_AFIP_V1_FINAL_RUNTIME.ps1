param([string]$ProjectRoot = "C:\AFIP", [int]$ObserveSeconds = 20)
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
function Read-Status {
  $raw = & .\STATUS_AFIP.ps1 | Out-String
  return $raw | ConvertFrom-Json
}
& .\STOP_AFIP.ps1 | Out-Null
& .\START_AFIP.ps1 | Out-Null
Start-Sleep -Seconds $ObserveSeconds
$running = Read-Status
if ($running.status -ne "RUNNING") { throw "AFIP is not RUNNING" }
if ($running.trading_runtime.router.running -ne $true) { throw "Router is not running" }
if ($running.research_runtime.process_state -ne "RUNNING") { throw "Research service is not running" }
if ($running.research_runtime.engine.status -ne "RUNNING") { throw "Research engine status is not RUNNING" }
if ($running.research_runtime.engine.execution_authority -eq $true) { throw "Research must not have execution authority" }
if ($running.dashboard.process_state -ne "RUNNING") { throw "Dashboard is not running" }
& .\STOP_AFIP.ps1 | Out-Null
$stopped = Read-Status
if ($stopped.status -ne "STOPPED") { throw "AFIP did not stop cleanly" }
if ($stopped.trading_runtime.router.state -ne "STOPPED") { throw "Router stale state" }
if ($stopped.research_runtime.process_state -ne "STOPPED") { throw "Research did not stop" }
if ($stopped.dashboard.process_state -ne "STOPPED") { throw "Dashboard did not stop" }
Write-Host "AFIP V1 Final Start/Run/Stop Certification: PASS"

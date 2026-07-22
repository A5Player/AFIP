param([string]$ProjectRoot = "C:\AFIP\source")
Set-Location $ProjectRoot
$pidFile = Join-Path $ProjectRoot "runtime\control\afip_research_background.pid"
if (Test-Path $pidFile) {
  $pidValue = [int](Get-Content $pidFile -ErrorAction SilentlyContinue)
  if ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) { Write-Host "Research: RUNNING | PID: $pidValue" } else { Write-Host "Research: STOPPED (stale PID file)" }
} else { Write-Host "Research: STOPPED" }
$status = Join-Path $ProjectRoot "runtime\research\automatic_research_status.json"
if (Test-Path $status) { Get-Content $status }

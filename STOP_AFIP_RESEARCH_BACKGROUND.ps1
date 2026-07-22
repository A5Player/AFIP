param([string]$ProjectRoot = "C:\AFIP\source", [int]$WaitSeconds = 30)
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$control = Join-Path $ProjectRoot "runtime\control"
New-Item -ItemType Directory -Force $control | Out-Null
$pidFile = Join-Path $control "afip_research_background.pid"
$stopFlag = Join-Path $control "stop_phase_v_major.flag"
Set-Content $stopFlag "stop"
if (Test-Path $pidFile) {
  $pidValue = [int](Get-Content $pidFile -ErrorAction SilentlyContinue)
  $deadline = (Get-Date).AddSeconds($WaitSeconds)
  while ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 1 }
  if (Get-Process -Id $pidValue -ErrorAction SilentlyContinue) { Stop-Process -Id $pidValue -Force; Write-Host "Research process forced to stop after timeout." }
  Remove-Item $pidFile -ErrorAction SilentlyContinue
}
Write-Host "AFIP background research stopped. Trading runtime was not changed."

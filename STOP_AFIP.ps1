param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){$Python='python'}

& $Python -m tools.afip_final_integration stop --root $ProjectRoot
if($LASTEXITCODE -ne 0){throw "AFIP STOP failed: $LASTEXITCODE"}

# Final lifecycle sweep: remove orphaned AFIP workers even when PID files or
# parent launcher processes are stale. MT5 terminal processes are never matched.
$Markers = @(
  'tools.afip_runtime_continuity_watchdog',
  'tools.afip_dashboard_monitor',
  'tools.afip_final_integration research-forever',
  'tools.afip_profile_sequential_execution_router'
)
$RootNeedle = $ProjectRoot.ToLowerInvariant()
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
Where-Object {
  $_.Name -eq 'python.exe' -and
  $_.CommandLine -and
  $_.CommandLine.ToLowerInvariant().Contains($RootNeedle) -and
  ($Markers | Where-Object { $_ -and $_.CommandLine })
} | ForEach-Object {
  $line = $_.CommandLine.ToLowerInvariant()
  $matched = $false
  foreach($marker in $Markers){ if($line.Contains($marker.ToLowerInvariant())){$matched=$true;break} }
  if($matched){ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

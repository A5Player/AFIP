param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$files = @(
  "afip\demo_execution_gateway\runtime.py",
  "tests\test_afip_v1_live_execution_trace_certification.py"
)
foreach ($relative in $files) {
  $source = Join-Path $PackRoot $relative
  $target = Join-Path $ProjectRoot $relative
  if (([IO.Path]::GetFullPath($source)) -eq ([IO.Path]::GetFullPath($target))) {
    Write-Host "Already in place: $relative"
    continue
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  Copy-Item -Force $source $target
  Write-Host "Installed: $relative"
}
Write-Host "AFIP V1 Live Execution Trace Certification installed."

param(
  [string]$ProjectRoot = "C:\AFIP"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Files = @(
  "afip\demo_execution_gateway\runtime.py",
  "tests\test_afip_v1_execution_intelligence_certification.py"
)
foreach ($Relative in $Files) {
  $Source = Join-Path $PackRoot $Relative
  $Target = Join-Path $ProjectRoot $Relative
  $TargetDir = Split-Path -Parent $Target
  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Relative"
}
Write-Host "AFIP V1 Execution Intelligence Certification installed."

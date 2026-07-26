param(
  [string]$ProjectRoot = "C:\AFIP"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }

$files = @(
  "afip\dashboard_data_contract.py",
  "afip\live_mt5_dashboard.py",
  "afip\dashboard_ui\split_runtime.py",
  "afip\dashboard_ui\live_service.py",
  "afip\four_profile_operations\mt5_connection.py",
  "tools\afip_mt5_multi_terminal_check.py",
  "tests\test_afip_v1_runtime_truth_passive_monitoring_final.py",
  "tests\test_afip_v1_dashboard_passive_truth_completion.py"
)
foreach ($relative in $files) {
  $source = Join-Path $PackRoot $relative
  $target = Join-Path $ProjectRoot $relative
  $parent = Split-Path -Parent $target
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Copy-Item -Force $source $target
  Write-Host "Installed: $relative"
}

Push-Location $ProjectRoot
try {
  $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (-not (Test-Path $python)) { $python = "python" }
  & $python -m py_compile `
    afip\dashboard_data_contract.py `
    afip\live_mt5_dashboard.py `
    afip\dashboard_ui\split_runtime.py `
    afip\dashboard_ui\live_service.py `
    afip\four_profile_operations\mt5_connection.py `
    tools\afip_mt5_multi_terminal_check.py
  & $python -m pytest `
    tests\test_afip_v1_runtime_truth_passive_monitoring_final.py `
    tests\test_afip_v1_dashboard_passive_truth_completion.py -q
  & $python tools\afip_mt5_multi_terminal_check.py
  & $python -m afip.dashboard_ui
  Write-Host "AFIP V1 Passive Monitoring Dashboard Truth Completion: PASS"
}
finally {
  Pop-Location
}

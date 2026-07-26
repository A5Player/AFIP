param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "AFIP V1 Runtime Truth & Passive Monitoring Final"
Write-Host "ProjectRoot: $ProjectRoot"
$files = @(
  "afip\four_profile_operations\mt5_connection.py",
  "afip\dashboard_ui\live_service.py",
  "afip\dashboard_ui\split_runtime.py",
  "afip\dashboard_data_contract.py",
  "afip\live_mt5_dashboard.py",
  "tools\afip_mt5_multi_terminal_check.py",
  "tests\test_afip_v1_runtime_truth_passive_monitoring_final.py"
)
foreach ($relative in $files) {
  $source = Join-Path $PackRoot $relative
  $target = Join-Path $ProjectRoot $relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  Copy-Item -Force $source $target
  Write-Host "Installed: $relative"
}
Set-Location $ProjectRoot
python -m py_compile afip\four_profile_operations\mt5_connection.py afip\dashboard_data_contract.py afip\live_mt5_dashboard.py afip\dashboard_ui\live_service.py afip\dashboard_ui\split_runtime.py tools\afip_mt5_multi_terminal_check.py
python -m pytest -q tests\test_afip_v1_runtime_truth_passive_monitoring_final.py tests\test_afip_v1_dashboard_data_contract_phase_1.py tests\test_phase_u_dashboard_live_mt5_fields.py tests\test_phase_u_final_dashboard_mt5_live.py
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Write-Host "PASS: passive monitoring installed. The default MT5 check no longer initializes terminals."

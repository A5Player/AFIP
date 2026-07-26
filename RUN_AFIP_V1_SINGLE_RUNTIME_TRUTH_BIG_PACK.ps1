param(
  [string]$ProjectRoot = "C:\AFIP"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "AFIP V1 Single Runtime Truth Big Pack" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path (Join-Path $ProjectRoot "afip"))) { throw "AFIP source folder not found: $ProjectRoot\afip" }

$files = @(
  "afip\runtime_truth.py",
  "afip\dashboard_data_contract.py",
  "afip\dashboard_ui\split_runtime.py",
  "afip\live_mt5_dashboard.py",
  "tests\test_afip_v1_single_runtime_truth_refactor.py",
  "README_AFIP_V1_SINGLE_RUNTIME_TRUTH_BIG_PACK.md",
  "FILE_LIST_AFIP_V1_SINGLE_RUNTIME_TRUTH_BIG_PACK.txt"
)

foreach ($rel in $files) {
  $src = Join-Path $PackRoot $rel
  $dst = Join-Path $ProjectRoot $rel
  $parent = Split-Path -Parent $dst
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Copy-Item -Force $src $dst
  Write-Host "Installed: $rel"
}

Push-Location $ProjectRoot
try {
  $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (-not (Test-Path $python)) { $python = "python" }

  & $python -m compileall afip\runtime_truth.py afip\dashboard_data_contract.py afip\dashboard_ui\split_runtime.py afip\live_mt5_dashboard.py
  if ($LASTEXITCODE -ne 0) { throw "Compile failed" }

  & $python -m pytest tests\test_afip_v1_single_runtime_truth_refactor.py tests\test_afip_v1_dashboard_data_contract_phase_1.py tests\test_afip_v1_dashboard_passive_truth_completion.py tests\test_afip_v1_runtime_truth_passive_monitoring_final.py -q
  if ($LASTEXITCODE -ne 0) { throw "Focused regression failed" }

  & $python tools\afip_mt5_multi_terminal_check.py
  $passiveExitCode = $LASTEXITCODE
  if ($passiveExitCode -ne 0) {
    Write-Warning "Passive MT5 observation returned exit code $passiveExitCode. This can be expected when one or more configured terminals are intentionally stopped. Continuing because passive observation is diagnostic and must not block dashboard generation."
  }

  & $python -m afip.dashboard_ui
  if ($LASTEXITCODE -ne 0) { throw "Dashboard generation failed" }

  Write-Host "AFIP V1 Single Runtime Truth Big Pack: PASS" -ForegroundColor Green
  Write-Host "Open: $ProjectRoot\runtime\dashboard\afip_dashboard.html"
}
finally {
  Pop-Location
}

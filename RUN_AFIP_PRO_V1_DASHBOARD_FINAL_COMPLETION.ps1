param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }
& $python -m py_compile afip\dashboard_ui\split_runtime.py afip\research_data_foundation\aggregator.py
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }
& $python -m pytest tests\test_afip_pro_v1_dashboard_final_completion.py -q
if ($LASTEXITCODE -ne 0) { throw "Focused regression failed" }
& $python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard generation failed" }
$html = Join-Path $ProjectRoot "runtime\dashboard\afip_research_data_dashboard.html"
if (-not (Test-Path $html)) { throw "Research dashboard was not generated" }
$content = Get-Content $html -Raw
foreach ($text in @("Research performance truth", "Research-to-trading connection audit", "SHOW TRUTH · NEVER INVENT METRICS")) {
  if ($content -notlike "*$text*") { throw "Dashboard validation missing: $text" }
}
Write-Host "AFIP Pro V1 Dashboard Final Completion: PASS"

param([string]$ProjectRoot = 'C:\AFIP\source')
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python -PathType Leaf)) { throw "Python venv not found: $Python" }
& $Python -m py_compile afip\control_center_runtime.py afip\dashboard_ui\control_center.py afip\dashboard_ui\dashboard_authority.py afip\dashboard_ui\home.py afip\dashboard_ui\__main__.py
if ($LASTEXITCODE -ne 0) { throw 'Compile failed' }
& $Python -m pytest tests\test_afip_v1_control_center_pack_1.py -q
if ($LASTEXITCODE -ne 0) { throw 'Focused tests failed' }
& $Python -m pytest tests\test_afip_v1_final_revision_1_compatibility.py tests\test_afip_v1_final_revision_2_1_dashboard_authority_merge.py tests\test_afip_v1_final_runtime_observatory.py -q
if ($LASTEXITCODE -ne 0) { throw 'Compatibility tests failed' }
& $Python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw 'Dashboard build failed' }
Write-Host 'Pack 1 validation PASS. Run full regression separately: .\.venv\Scripts\python.exe -m pytest -q'

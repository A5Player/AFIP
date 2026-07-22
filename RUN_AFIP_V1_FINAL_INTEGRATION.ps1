param([string]$ProjectRoot = "C:\AFIP\source",[switch]$FullRegression)
$ErrorActionPreference="Stop"; Set-Location $ProjectRoot
$python=Join-Path $ProjectRoot ".venv\Scripts\python.exe"; if(-not(Test-Path $python)){throw "Python venv not found: $python"}
& $python -m pytest tests/test_afip_v1_final_integration.py tests/test_revision_4_research_separation.py tests/test_afip_v1_final_runtime_observatory.py -q
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& $python -m tools.afip_final_integration research-once --root $ProjectRoot
& $python -m tools.afip_final_integration dashboard --root $ProjectRoot
& $python tools/validate_financial_naming.py
& $python tools/afip_local_quality_check.py
& $python afip.py mt5-check
if($FullRegression){& $python -m pytest -q}

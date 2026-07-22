param([switch]$FullRegression,[string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop';Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe';if(-not(Test-Path $Python)){$Python='python'}
& $Python -m pytest tests/test_afip_v1_final_consolidation.py -q;if($LASTEXITCODE -ne 0){throw 'Final consolidation tests failed'}
$Optional=@('tests/test_revision_4_research_separation.py','tests/test_revision_3_replay_throughput.py','tests/test_afip_v1_final_runtime_observatory.py')
foreach($Test in $Optional){if(Test-Path $Test){& $Python -m pytest $Test -q;if($LASTEXITCODE -ne 0){throw "Compatibility test failed: $Test"}}}
& $Python -m tools.afip_final_integration architecture --root $ProjectRoot
& $Python -m tools.afip_final_integration dashboard --root $ProjectRoot
if(Test-Path 'tools/validate_financial_naming.py'){& $Python tools/validate_financial_naming.py;if($LASTEXITCODE -ne 0){throw 'Financial naming failed'}}
if(Test-Path 'tools/afip_local_quality_check.py'){& $Python tools/afip_local_quality_check.py;if($LASTEXITCODE -ne 0){throw 'Local quality failed'}}
if($FullRegression){& $Python -m pytest -q;if($LASTEXITCODE -ne 0){throw 'Full regression failed'}}
Write-Host 'AFIP V1 FINAL CONSOLIDATION VALIDATION PASS'

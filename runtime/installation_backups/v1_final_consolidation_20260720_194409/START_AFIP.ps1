param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'; Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'; if(-not(Test-Path $Python)){$Python='python'}
& $Python -m tools.afip_final_integration start --root $ProjectRoot
if($LASTEXITCODE -ne 0){throw "AFIP START failed: $LASTEXITCODE"}

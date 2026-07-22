param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Continue'; Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'; if(-not(Test-Path $Python)){$Python='python'}
& $Python -m tools.afip_verify_account_isolation --output runtime\account_isolation_status.json
exit $LASTEXITCODE

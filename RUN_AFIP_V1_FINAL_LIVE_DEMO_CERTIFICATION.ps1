$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "AFIP V1 Final Live Demo Certification"
Write-Host "Safety: READ ONLY | NO ORDER CHECK | NO ORDER SEND"

python -m pytest -q tests/test_afip_v1_final_live_demo_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_v1_final_live_demo_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "AFIP V1 FINAL: PRODUCTION CERTIFICATION PASS"
exit 0

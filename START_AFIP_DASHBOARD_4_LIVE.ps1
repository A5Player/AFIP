$ErrorActionPreference = "Stop"
Write-Host "AFIP Professional Dashboard 4 - Live Builder" -ForegroundColor Cyan
while ($true) {
    & $PSScriptRoot\.venv\Scripts\python.exe -m afip.dashboard_ui
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed with exit code $LASTEXITCODE" }
    Start-Sleep -Seconds 10
}

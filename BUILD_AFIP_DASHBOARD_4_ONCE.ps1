$ErrorActionPreference = "Stop"
& $PSScriptRoot\.venv\Scripts\python.exe -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed with exit code $LASTEXITCODE" }
Start-Process "$PSScriptRoot\runtime\dashboard\afip_dashboard.html"

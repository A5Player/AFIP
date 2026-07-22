$ErrorActionPreference = "Stop"
$obsolete = @(
  "afip\dashboard_ui\live_research_dashboard.py",
  "tools\afip_live_dashboard_4.py"
)
foreach ($item in $obsolete) {
  $path = Join-Path $PSScriptRoot $item
  if (Test-Path $path) { Remove-Item $path -Force }
}
Write-Host "Broken raw-JSON dashboard hotfix files removed." -ForegroundColor Green

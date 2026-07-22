param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$pidFile = Join-Path $ProjectRoot "runtime\control\afip_research_background.pid"
if (Test-Path $pidFile) {
  $pidValue = [int](Get-Content $pidFile -ErrorAction SilentlyContinue)
  if ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) { throw "Stop AFIP research first. Active PID: $pidValue" }
}
$backup = Join-Path $ProjectRoot "_revision4_backup"
New-Item -ItemType Directory -Force $backup | Out-Null
$files = @(
 "afip\automatic_research_runtime\runtime.py",
 "tests\test_revision_4_research_separation.py",
 "START_AFIP_RESEARCH_BACKGROUND.ps1",
 "STOP_AFIP_RESEARCH_BACKGROUND.ps1",
 "STATUS_AFIP_RESEARCH_BACKGROUND.ps1"
)
foreach ($rel in $files) {
  $src = Join-Path $packageRoot $rel; $dst = Join-Path $ProjectRoot $rel
  if (Test-Path $dst) { $bak = Join-Path $backup $rel; New-Item -ItemType Directory -Force (Split-Path $bak -Parent) | Out-Null; Copy-Item $dst $bak -Force }
  New-Item -ItemType Directory -Force (Split-Path $dst -Parent) | Out-Null
  Copy-Item $src $dst -Force
  Write-Host "Installed: $rel"
}
Write-Host "Revision 4 installation complete. Backup: $backup"

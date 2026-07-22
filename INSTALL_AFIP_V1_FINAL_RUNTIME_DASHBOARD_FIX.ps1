param([string]$ProjectRoot = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$PackRoot = $PSScriptRoot

if (-not (Test-Path (Join-Path $ProjectRoot 'afip'))) {
    throw "AFIP repository not found at $ProjectRoot. Extract this ZIP directly into C:\AFIP\source and run again."
}

$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }

Write-Host "AFIP V1 Final Runtime & Dashboard Fix" -ForegroundColor Cyan
Write-Host "1/6 Stopping existing AFIP processes safely..."
$StopScript = Join-Path $ProjectRoot 'STOP_AFIP.ps1'
if (Test-Path $StopScript) {
    try { & $StopScript -ProjectRoot $ProjectRoot | Out-Host } catch { Write-Warning $_ }
}

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup = Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_RUNTIME_DASHBOARD_FIX_$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Files = @(
    'afip\production_certification\incremental_financial_naming.py',
    'afip\production_certification\runtime.py',
    'afip\final_integration\dashboard.py',
    'afip\final_integration\runtime.py',
    'afip\dashboard_ui\dashboard_authority.py',
    'afip\dashboard_ui\research_operations.py',
    'tools\afip_final_integration.py'
)

Write-Host "2/6 Backing up and installing the final files..."
foreach ($Relative in $Files) {
    $Source = Join-Path $PackRoot $Relative
    $Target = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path $Source)) { throw "Missing pack file: $Relative" }

    $SourceFull = [System.IO.Path]::GetFullPath($Source).TrimEnd('\')
    $TargetFull = [System.IO.Path]::GetFullPath($Target).TrimEnd('\')
    if ([string]::Equals($SourceFull, $TargetFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Host "  Already installed: $Relative"
        continue
    }

    if (Test-Path $Target) {
        $BackupTarget = Join-Path $Backup $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path $BackupTarget) | Out-Null
        Copy-Item $Target $BackupTarget -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
    Copy-Item $Source $Target -Force
}

Write-Host "3/6 Removing stale Python cache and old generated dashboard output..."
Get-ChildItem (Join-Path $ProjectRoot 'afip') -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem (Join-Path $ProjectRoot 'tools') -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
$DashboardDir = Join-Path $ProjectRoot 'runtime\dashboard'
New-Item -ItemType Directory -Force -Path $DashboardDir | Out-Null
Get-ChildItem $DashboardDir -Filter 'afip_*dashboard.html' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "4/6 Building the one canonical dashboard..."
Push-Location $ProjectRoot
try {
    & $Python -m tools.afip_final_integration dashboard --root $ProjectRoot | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed with exit code $LASTEXITCODE" }

    Write-Host "5/6 Recording fast non-blocking financial naming audit..."
    $AuditCode = @'
import json
from pathlib import Path
from afip.production_certification.incremental_financial_naming import run_incremental_financial_naming
root = Path(r"__PROJECT_ROOT__")
print(json.dumps(run_incremental_financial_naming(root, force=False), ensure_ascii=False, indent=2))
'@.Replace('__PROJECT_ROOT__', $ProjectRoot.Replace('\', '\\'))
    try {
        $AuditCode | & $Python - | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Warning "Financial naming audit returned exit code $LASTEXITCODE; runtime startup will continue." }
    } catch {
        Write-Warning "Financial naming audit could not run; runtime startup will continue: $_"
    }

    Write-Host "6/6 Starting AFIP trading, background research and live dashboard monitor..."
    & (Join-Path $ProjectRoot 'START_AFIP.ps1') -ProjectRoot $ProjectRoot | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "AFIP start failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$Dashboard = Join-Path $ProjectRoot 'runtime\dashboard\afip_dashboard.html'
if (-not (Test-Path $Dashboard)) { throw "Canonical dashboard was not generated: $Dashboard" }
Start-Process $Dashboard

Write-Host "" 
Write-Host "AFIP FINAL FIX INSTALLED AND STARTED" -ForegroundColor Green
Write-Host "Dashboard: $Dashboard"
Write-Host "Background dashboard refresh: every 5 seconds"
Write-Host "Research and dashboard processes do not block trading startup."
Write-Host "Backup: $Backup"

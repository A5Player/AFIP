$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host 'AFIP V1 Final Capital Tier Policy Correction' -ForegroundColor Cyan
Write-Host 'Safety: this installer does not start AFIP automatically.' -ForegroundColor Yellow

if (Test-Path '.\STOP_AFIP.ps1') {
    Write-Host '1/5 Stopping AFIP safely...'
    & '.\STOP_AFIP.ps1'
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $Root "backup\AFIP_V1_FINAL_CAPITAL_TIER_POLICY_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null

$files = @(
    'config\four_profile_demo.json',
    'afip\lot_authority\runtime.py',
    'afip\demo_execution_gateway\runtime.py',
    'tests\test_afip_final_capital_tier_authority.py'
)

Write-Host '2/5 Backing up and installing corrected files...'
foreach ($relative in $files) {
    $source = Join-Path $Root $relative
    $target = Join-Path $Root $relative
    $backupTarget = Join-Path $backup $relative
    if (Test-Path $target) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $backupTarget) -Force | Out-Null
        Copy-Item $target $backupTarget -Force
    }
    # Files are already in their final paths when the ZIP is extracted over the repository.
    Write-Host "  Installed: $relative"
}

Write-Host '3/5 Removing stale Python cache...'
Get-ChildItem -Path '.\afip' -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host '4/5 Verifying obsolete sizing fields are absent from the active policy...'
$configText = Get-Content '.\config\four_profile_demo.json' -Raw
if ($configText -match '"capital_per_unit"' -or $configText -match '"capital_per_unit_legacy_only"') {
    throw 'Obsolete capital-per-unit policy still exists in config\four_profile_demo.json'
}

$python = '.\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }

Write-Host '5/5 Running exact policy regression...'
& $python -m pytest tests\test_afip_final_capital_tier_authority.py -q
if ($LASTEXITCODE -ne 0) { throw 'Capital tier policy regression failed.' }

Write-Host ''
Write-Host 'CAPITAL TIER POLICY CORRECTION INSTALLED' -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host 'AFIP remains STOPPED. Keep Algo Trading OFF until account isolation is verified.' -ForegroundColor Yellow
Write-Host 'Then start only with: .\START_AFIP_SAFE.ps1'

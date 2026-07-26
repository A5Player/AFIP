[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".git")) {
    throw "Not a Git repository: $ProjectRoot"
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found: $ProjectRoot\.venv"
}

Write-Host "AFIP V1 Final Production Certification Pack 2 - Revision 1"
Write-Host "============================================="

Write-Step "Installing source-level dashboard bottom safety contract"
$sourceModule = Join-Path $PackRoot "afip\dashboard_bottom_safety.py"
$targetModule = Join-Path $ProjectRoot "afip\dashboard_bottom_safety.py"

$sourceFull = [System.IO.Path]::GetFullPath($sourceModule)
$targetFull = [System.IO.Path]::GetFullPath($targetModule)

if ($sourceFull -ieq $targetFull) {
    Write-Host "Source module already installed in project root; copy skipped."
} else {
    Copy-Item -LiteralPath $sourceModule -Destination $targetModule -Force
    Write-Host "Installed: afip/dashboard_bottom_safety.py"
}

Write-Step "Binding contract repair to the real dashboard entry point"
$entryPoint = Join-Path $ProjectRoot "afip\dashboard_ui\__main__.py"
if (-not (Test-Path -LiteralPath $entryPoint)) {
    throw "Dashboard entry point not found: $entryPoint"
}

$bindingMarker = "# AFIP_V1_BOTTOM_SAFETY_CONTRACT"
$binding = @'

# AFIP_V1_BOTTOM_SAFETY_CONTRACT
from afip.dashboard_bottom_safety import ensure_primary_dashboard_bottom_safety as _afip_ensure_bottom_safety
_afip_ensure_bottom_safety()
'@

$current = Get-Content -LiteralPath $entryPoint -Raw
if ($current -notmatch [regex]::Escape($bindingMarker)) {
    Add-Content -LiteralPath $entryPoint -Value $binding -Encoding UTF8
    Write-Host "Bound dashboard bottom safety contract."
} else {
    Write-Host "Dashboard bottom safety contract already bound."
}

Write-Step "Generating primary dashboards through the real entry point"
& ".venv\Scripts\python.exe" -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard generation failed."
}

Write-Step "Applying contract to all currently available primary dashboards"
& ".venv\Scripts\python.exe" -m afip.dashboard_bottom_safety
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard bottom safety repair failed."
}

Write-Step "Running exact regression"
& ".venv\Scripts\python.exe" -m pytest `
    "tests/test_afip_v1_dashboard_layout_completion_pack.py::test_all_primary_pages_have_bottom_safety_space" -q
if ($LASTEXITCODE -ne 0) {
    throw "Exact dashboard layout regression still fails."
}

Write-Step "Running dashboard layout certification file"
& ".venv\Scripts\python.exe" -m pytest `
    "tests/test_afip_v1_dashboard_layout_completion_pack.py" -q
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard layout certification failed."
}

Write-Step "Running Git whitespace validation"
& git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed."
}

Write-Host ""
Write-Host "PASS: AFIP V1 Final Production Certification Pack 2 completed." -ForegroundColor Green
Write-Host ""
Write-Host "Run full regression next:"
Write-Host "  python -m pytest"
Write-Host ""
Write-Host "After 2762 passed:"
Write-Host "  git add ."
Write-Host "  git status"
Write-Host '  git commit -m "AFIP V1 Final Production Certification"'
Write-Host "  git push origin main"

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

function Test-GitTracked {
    param([string]$Path)

    # Do not use --error-unmatch here. With $ErrorActionPreference = "Stop",
    # Git's normal "not tracked" stderr can become a terminating PowerShell error.
    $trackedPath = & git ls-files -- $Path 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files failed while checking: $Path"
    }

    return (-not [string]::IsNullOrWhiteSpace(($trackedPath -join "")))
}

Write-Host "AFIP V1 Final Production Certification - Revision 1"
Write-Host "======================================="

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".git")) {
    throw "Not a Git repository: $ProjectRoot"
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    throw "AFIP virtual environment not found: $ProjectRoot\.venv"
}

Write-Step "Restoring accidentally deleted tracked archive, when applicable"
$trackedArchive = "AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip"
if (Test-GitTracked $trackedArchive) {
    $statusLine = (& git status --porcelain -- $trackedArchive)
    if ($statusLine -match '^\s*D|^D') {
        & git restore -- $trackedArchive
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to restore tracked archive: $trackedArchive"
        }
        Write-Host "Restored: $trackedArchive"
    } else {
        Write-Host "Archive is not deleted; no restore required."
    }
} else {
    Write-Host "Archive is not tracked in this checkout; no action taken."
}

Write-Step "Restoring generated tracked runtime snapshots"
$generatedTracked = @(
    "runtime/certification/financial_naming_report.json",
    "runtime/dashboard/afip_control_center.html",
    "runtime/dashboard/afip_dashboard.html",
    "runtime/dashboard/afip_intelligence_engine_dashboard.html",
    "runtime/dashboard/afip_profiles_dashboard.html",
    "runtime/dashboard/afip_research_data_dashboard.html",
    "runtime/dashboard/afip_research_operations_dashboard.html",
    "runtime/dashboard/production_authority_snapshot.json",
    "runtime/profiles/p1/mt5_health.json",
    "runtime/profiles/p2/mt5_health.json",
    "runtime/profiles/p3/mt5_health.json",
    "runtime/profiles/p4/mt5_health.json"
)

foreach ($item in $generatedTracked) {
    if (Test-GitTracked $item) {
        $itemStatus = (& git status --porcelain -- $item)
        if ($itemStatus) {
            & git restore -- $item
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to restore generated tracked file: $item"
            }
            Write-Host "Restored generated snapshot: $item"
        }
    }
}

Write-Step "Removing untracked runtime-only output"
$runtimeOnly = @(
    "runtime/dashboard/afip_dashboard_audit.html",
    "runtime/dashboard/afip_dashboard_completeness.html",
    "runtime/dashboard/afip_execution_pipeline_dashboard.html",
    "runtime/dashboard/afip_live_mt5_dashboard.html",
    "runtime/dashboard/afip_order_evidence_dashboard.html",
    "runtime/dashboard/afip_research_observability_dashboard.html",
    "runtime/dashboard/afip_unified_dashboard.html",
    "runtime/dashboard/dashboard_runtime.json",
    "runtime/profiles/p1/mt5_live_snapshot.json",
    "runtime/profiles/p2/mt5_live_snapshot.json",
    "runtime/profiles/p3/mt5_live_snapshot.json",
    "runtime/profiles/p4/mt5_live_snapshot.json"
)

foreach ($item in $runtimeOnly) {
    if ((Test-Path -LiteralPath $item) -and -not (Test-GitTracked $item)) {
        Remove-Item -LiteralPath $item -Force
        Write-Host "Removed runtime-only output: $item"
    }
}

Write-Step "Removing extracted patch workspace and local audit output"
$localOnly = @(
    "AFIP_MAXIMUM_LOT_AUTHORITY_FINAL_PATCH",
    "AFIP_CAPITAL_AUTHORITY_AUDIT.txt"
)

foreach ($item in $localOnly) {
    if ((Test-Path -LiteralPath $item) -and -not (Test-GitTracked $item)) {
        Remove-Item -LiteralPath $item -Recurse -Force
        Write-Host "Removed local-only item: $item"
    }
}

Write-Step "Adding exact transient exclusions to .gitignore"
$ignoreEntries = @(
    "",
    "# AFIP V1 runtime-only generated state",
    "/runtime/dashboard/dashboard_runtime.json",
    "/runtime/profiles/*/mt5_live_snapshot.json",
    "/AFIP_MAXIMUM_LOT_AUTHORITY_FINAL_PATCH/",
    "/AFIP_CAPITAL_AUTHORITY_AUDIT.txt"
)

$gitignorePath = Join-Path $ProjectRoot ".gitignore"
if (-not (Test-Path -LiteralPath $gitignorePath)) {
    New-Item -ItemType File -Path $gitignorePath -Force | Out-Null
}

$currentIgnore = Get-Content -LiteralPath $gitignorePath -Raw -ErrorAction SilentlyContinue
foreach ($entry in $ignoreEntries) {
    if ([string]::IsNullOrEmpty($entry)) {
        continue
    }
    if ($currentIgnore -notmatch [regex]::Escape($entry)) {
        Add-Content -LiteralPath $gitignorePath -Value $entry -Encoding UTF8
        $currentIgnore += "`r`n$entry"
    }
}

Write-Step "Running final repository audit"
& ".venv\Scripts\python.exe" "tools\afip_v1_final_production_certification.py" --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Final repository audit failed."
}

Write-Step "Running Git whitespace validation"
& git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed. Resolve whitespace errors before commit."
}

Write-Step "Focused production certification"
$focusedTests = @(
    "tests/test_afip_v1_runtime_truth_contract_final.py",
    "tests/test_afip_v1_dashboard_runtime_truth_preflight.py",
    "tests/test_afip_v1_single_runtime_truth_refactor.py",
    "tests/test_afip_final_capital_tier_authority.py",
    "tests/test_afip_v1_final_maximum_lot_size_unit_policy.py",
    "tests/test_afip_final_execution_ownership.py",
    "tests/test_afip_account_isolation_capital_safety.py"
)

& ".venv\Scripts\python.exe" -m pytest @focusedTests -q
if ($LASTEXITCODE -ne 0) {
    throw "Focused production certification failed."
}

Write-Host ""
Write-Host "PASS: AFIP V1 repository cleanup and focused production certification completed." -ForegroundColor Green
Write-Host ""
Write-Host "Next commands:"
Write-Host "  git status"
Write-Host "  git diff --stat"
Write-Host "  python -m pytest"
Write-Host "  git add ."
Write-Host '  git commit -m "AFIP V1 Final Production Certification"'
Write-Host "  git push origin main"

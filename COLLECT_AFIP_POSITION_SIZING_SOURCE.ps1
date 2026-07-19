param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputZip = ""
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo "afip"))) {
    throw "AFIP repository not found: $repo"
}
if (-not (Test-Path (Join-Path $repo "config\four_profile_demo.json"))) {
    throw "Missing config\four_profile_demo.json"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if ([string]::IsNullOrWhiteSpace($OutputZip)) {
    $OutputZip = Join-Path $repo "AFIP_POSITION_SIZING_SOURCE_$stamp.zip"
}

$temp = Join-Path $env:TEMP "AFIP_POSITION_SIZING_SOURCE_$stamp"
New-Item -ItemType Directory -Force -Path $temp | Out-Null

$required = @(
    "afip\position_capacity_formula.py",
    "afip\capital_growth_engine\runtime.py",
    "afip\unit_allocation\models.py",
    "afip\unit_allocation\runtime.py",
    "afip\demo_execution_gateway\runtime.py",
    "afip\execution_safety\capital_aware_protection_guard.py",
    "afip\complete_trade_plan\runtime.py",
    "afip\trade_plan_runtime\runtime.py",
    "afip\four_profile_operations\runtime.py",
    "afip\dashboard_ui\runtime.py",
    "afip\dashboard_ui\split_runtime.py",
    "config\four_profile_demo.json"
)

$optionalPatterns = @(
    "tests\*position*capacity*.py",
    "tests\*capital*growth*.py",
    "tests\*unit*allocation*.py",
    "tests\*demo*execution*gateway*.py",
    "tests\*capital*aware*.py",
    "tests\*complete*trade*plan*.py",
    "tests\*milestone*s*pack*5*5*.py"
)

$copied = New-Object System.Collections.Generic.List[string]
$missing = New-Object System.Collections.Generic.List[string]

foreach ($relative in $required) {
    $source = Join-Path $repo $relative
    if (Test-Path $source) {
        $destination = Join-Path $temp $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
        Copy-Item $source $destination -Force
        $copied.Add($relative)
    } else {
        $missing.Add($relative)
    }
}

foreach ($pattern in $optionalPatterns) {
    Get-ChildItem -Path (Join-Path $repo $pattern) -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            $relative = $_.FullName.Substring($repo.Length).TrimStart('\')
            $destination = Join-Path $temp $relative
            New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
            Copy-Item $_.FullName $destination -Force
            $copied.Add($relative)
        }
}

$gitInfo = @()
try {
    $gitInfo += "HEAD=" + (& git -C $repo rev-parse HEAD)
    $gitInfo += "BRANCH=" + (& git -C $repo branch --show-current)
    $gitInfo += "STATUS:"
    $gitInfo += (& git -C $repo status --short)
} catch {
    $gitInfo += "Git information unavailable: $($_.Exception.Message)"
}
$gitInfo | Set-Content (Join-Path $temp "GIT_STATE.txt") -Encoding UTF8

$manifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    repository_root = $repo
    copied_files = @($copied | Sort-Object -Unique)
    missing_required_files = @($missing)
}
$manifest | ConvertTo-Json -Depth 10 |
    Set-Content (Join-Path $temp "SOURCE_COLLECTION_MANIFEST.json") -Encoding UTF8

if ($missing.Count -gt 0) {
    Write-Warning ("Missing files: " + ($missing -join ", "))
}

if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}
Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $OutputZip -CompressionLevel Optimal
Remove-Item $temp -Recurse -Force

Write-Host ""
Write-Host "AFIP position sizing source package created:" -ForegroundColor Green
Write-Host $OutputZip -ForegroundColor Cyan
Write-Host ""
Write-Host "Upload this ZIP to ChatGPT for the clean overwrite patch." -ForegroundColor Yellow

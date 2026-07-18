$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone S Cleanup Pack 4.2.1 ==="
Write-Host "Documentation financial naming hotfix only."

Set-Location $PSScriptRoot

$targets = @(
    "HANDOFF_MILESTONE_S_CLEANUP_PACK_4_2.md",
    "README_MILESTONE_S_CLEANUP_PACK_4_2.md",
    "README_MILESTONE_S_CLEANUP_PACK_4_2_TH.md"
)

foreach ($relativePath in $targets) {
    $path = Join-Path $PSScriptRoot $relativePath

    if (-not (Test-Path $path)) {
        throw "Required documentation file not found: $relativePath"
    }

    $content = Get-Content -Path $path -Raw -Encoding UTF8
    $updated = [regex]::Replace(
        $content,
        "\bGuard\b",
        "Protection Control",
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if ($updated -ne $content) {
        Set-Content -Path $path -Value $updated -Encoding UTF8
        Write-Host "Updated: $relativePath"
    }
    else {
        Write-Host "No forbidden term found: $relativePath"
    }
}

Get-ChildItem -Path $PSScriptRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Remove-Item -Recurse -Force (Join-Path $PSScriptRoot ".pytest_cache") -ErrorAction SilentlyContinue

Write-Host "Running financial naming validation..."
& ".\.venv\Scripts\python.exe" "tools\validate_financial_naming.py"
if ($LASTEXITCODE -ne 0) {
    throw "Financial naming validation failed."
}

Write-Host "Running affected focused tests..."
& ".\.venv\Scripts\python.exe" -m pytest `
    "tests\phase2\test_afip_intelligence_naming.py" `
    "tests\test_milestone_s_cleanup_pack_4_2.py" `
    "tests\test_production_sprint8_real_confidence_calibration.py" -v

if ($LASTEXITCODE -ne 0) {
    throw "Pack 4.2.1 focused regression failed."
}

Write-Host ""
Write-Host "AFIP Milestone S Cleanup Pack 4.2.1 completed."
Write-Host "Execution remains STOPPED."
Write-Host "Next: run full pytest."

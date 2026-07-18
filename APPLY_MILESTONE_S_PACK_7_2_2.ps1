$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone S Pack 7.2.2 Apply ==="

$obsoleteFiles = @(
    "README_MILESTONE_S_PACK_7_2_1_TH.md",
    "RUN_MILESTONE_S_PACK_7_2_1.ps1",
    "VALIDATION_MILESTONE_S_PACK_7_2_1.txt"
)

foreach ($file in $obsoleteFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "Removed obsolete Pack 7.2.1 file: $file"
    }
}

Write-Host "Pack 7.2.2 cleanup completed."

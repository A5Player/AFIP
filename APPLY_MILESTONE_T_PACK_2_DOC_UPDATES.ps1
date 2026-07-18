$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$updates = @(
    @{ Source = "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_2_APPEND.md"; Target = "AFIP_PROJECT_DATABASE.md" },
    @{ Source = "HANDOFF_MILESTONE_T_PACK_2_APPEND.md"; Target = "HANDOFF.md" }
)
foreach ($update in $updates) {
    $sourcePath = Join-Path $root $update.Source
    $targetPath = Join-Path $root $update.Target
    $marker = "## Milestone T Pack 2"
    $content = Get-Content -Raw -Encoding UTF8 $sourcePath
    if (Test-Path $targetPath) {
        $existing = Get-Content -Raw -Encoding UTF8 $targetPath
        if ($existing.Contains($marker)) {
            Write-Host "Skipped $($update.Target) (already updated)"
            continue
        }
    }
    Add-Content -Path $targetPath -Value $content -Encoding UTF8
    Write-Host "Updated $($update.Target)"
}

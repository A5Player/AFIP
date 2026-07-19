param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

Write-Host "=== AFIP Phase U Pack 3.3.11 Apply ===" -ForegroundColor Cyan
Write-Host "Runtime Research Data Git Isolation" -ForegroundColor Cyan
Write-Host "Local/VPS data files will NOT be deleted." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    throw "RepositoryRoot is not a Git repository: $repo"
}

$generatedResearchFiles = @(
    "runtime/research/automatic/schema_v2/candidates.jsonl",
    "runtime/research/automatic/schema_v2/decisions.jsonl",
    "runtime/research/automatic/schema_v2/run_summaries.jsonl",
    "runtime/research/automatic/schema_v2/snapshots.jsonl",
    "runtime/research/automatic/schema_v2/timeline.jsonl"
)

foreach ($path in $generatedResearchFiles) {
    git rm --cached --ignore-unmatch -- "$path"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to remove runtime research file from Git index: $path"
    }
}

Write-Host ""
Write-Host "Runtime files remain on disk and are now protected by .gitignore." -ForegroundColor Green
Write-Host "Review with: git status" -ForegroundColor Green

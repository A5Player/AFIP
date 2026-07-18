$ErrorActionPreference = "Stop"
$projectAppend = Get-Content -Raw "AFIP_PROJECT_DATABASE_PACK_7_2_APPEND.md"
$handoffAppend = Get-Content -Raw "HANDOFF_PACK_7_2_APPEND.md"
if (-not (Select-String -Path "AFIP_PROJECT_DATABASE.md" -Pattern "Milestone S Pack 7.2" -Quiet)) {
    Add-Content -Path "AFIP_PROJECT_DATABASE.md" -Value "`r`n$projectAppend"
}
if (-not (Select-String -Path "HANDOFF.md" -Pattern "Milestone S Pack 7.2" -Quiet)) {
    Add-Content -Path "HANDOFF.md" -Value "`r`n$handoffAppend"
}
Write-Host "Pack 7.2 documentation updates applied."

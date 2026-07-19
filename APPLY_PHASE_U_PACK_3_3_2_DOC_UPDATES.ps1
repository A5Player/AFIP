$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
function Append-Once {
    param([string]$Target, [string]$Source, [string]$Marker)
    if (-not (Test-Path $Source)) { throw "Missing append source: $Source" }
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target -Force | Out-Null }
    $found = Select-String -Path $Target -SimpleMatch -Pattern $Marker -Quiet
    if ($found) { Write-Host "Already applied: $Marker"; return }
    [System.IO.File]::AppendAllText((Resolve-Path $Target), [System.IO.File]::ReadAllText((Resolve-Path $Source)), [System.Text.UTF8Encoding]::new($false))
    Write-Host "Appended $Source to $Target"
}
Append-Once -Target "AFIP_PROJECT_DATABASE.md" -Source "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_2_APPEND.md" -Marker "Phase U Pack 3.3.2"
Append-Once -Target "HANDOFF.md" -Source "HANDOFF_PHASE_U_PACK_3_3_2_APPEND.md" -Marker "Phase U Pack 3.3.2 Handoff"
Write-Host "Documentation update completed."

param(
    [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$BackupRoot = Join-Path $ProjectRoot "_revision3_backup"

$Files = @(
    "afip\automatic_research_runtime\runtime.py",
    "tests\test_revision_3_replay_throughput.py"
)

foreach ($RelativePath in $Files) {
    $Source = Join-Path $PackRoot $RelativePath
    $Destination = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path $Source)) { throw "Patch source missing: $Source" }

    $DestinationDirectory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null

    if (Test-Path $Destination) {
        $Backup = Join-Path $BackupRoot $RelativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $Backup) -Force | Out-Null
        Copy-Item $Destination $Backup -Force
    }
    Copy-Item $Source $Destination -Force
    Write-Host "Installed: $RelativePath"
}

Write-Host "Revision 3 installation complete."
Write-Host "Backup root: $BackupRoot"

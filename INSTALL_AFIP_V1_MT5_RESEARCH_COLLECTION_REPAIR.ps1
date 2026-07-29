param(
    [string]$ProjectRoot = "C:\AFIP"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot = Join-Path $PackRoot "payload"
$SourceRuntime = Join-Path $PayloadRoot "afip\automatic_research_runtime\runtime.py"
$SourceTest = Join-Path $PayloadRoot "tests\test_afip_v1_mt5_research_collection_repair.py"
$TargetRuntime = Join-Path $ProjectRoot "afip\automatic_research_runtime\runtime.py"
$TargetTest = Join-Path $ProjectRoot "tests\test_afip_v1_mt5_research_collection_repair.py"

if (-not (Test-Path $ProjectRoot)) {
    throw "AFIP project root not found: $ProjectRoot"
}
if (-not (Test-Path $SourceRuntime)) {
    throw "Patch payload missing: $SourceRuntime"
}
if (-not (Test-Path $TargetRuntime)) {
    throw "Real AFIP source file not found: $TargetRuntime"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "runtime\patch_backups\mt5_research_collection_repair_$Timestamp"
New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot "afip\automatic_research_runtime") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot "tests") | Out-Null

Copy-Item -Force $TargetRuntime (Join-Path $BackupRoot "afip\automatic_research_runtime\runtime.py")
if (Test-Path $TargetTest) {
    Copy-Item -Force $TargetTest (Join-Path $BackupRoot "tests\test_afip_v1_mt5_research_collection_repair.py")
}

Copy-Item -Force $SourceRuntime $TargetRuntime
Copy-Item -Force $SourceTest $TargetTest

Write-Host "Installed: afip/automatic_research_runtime/runtime.py"
Write-Host "Installed: tests/test_afip_v1_mt5_research_collection_repair.py"
Write-Host "Backup: $BackupRoot"
Write-Host "AFIP V1 MT5 Research Collection Repair installed successfully."

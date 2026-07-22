$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) { throw "Run this installer from C:\AFIP\source (repository root)." }
$Files = @(
"afip/runtime_observatory.py",
"afip/historical_replay_research/runtime.py",
"afip/automatic_research_runtime/runtime.py",
"afip/phase_v_major/__init__.py",
"afip/dashboard_ui/research_operations.py",
"afip/dashboard_ui/split_runtime.py",
"afip/dashboard_ui/authority_snapshot.py",
"tests/test_afip_v1_final_runtime_observatory.py",
"README_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.md",
"README_AFIP_V1_FINAL_RUNTIME_OBSERVATORY_TH.md",
"FILE_LIST_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.md",
"VALIDATION_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.md",
"RUN_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.ps1",
"RUN_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.bat",
"AFIP_PROJECT_DATABASE_V1_FINAL_RUNTIME_OBSERVATORY_APPEND.md",
"HANDOFF_AFIP_V1_FINAL_RUNTIME_OBSERVATORY_APPEND.md"
)
$Backup = Join-Path $RepoRoot ("backup\AFIP_V1_FINAL_RUNTIME_OBSERVATORY_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
foreach ($Relative in $Files) {
  $Source = Join-Path $PatchRoot $Relative
  if (-not (Test-Path $Source)) { throw "Patch file missing: $Relative" }
  $Target = Join-Path $RepoRoot $Relative
  if (Test-Path $Target) {
    $BackupTarget = Join-Path $Backup $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path $BackupTarget -Parent) | Out-Null
    Copy-Item -Force $Target $BackupTarget
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Target -Parent) | Out-Null
  Copy-Item -Force $Source $Target
}
Write-Host "AFIP V1 Final Runtime Observatory patch applied." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Next: .\RUN_AFIP_V1_FINAL_RUNTIME_OBSERVATORY.ps1"

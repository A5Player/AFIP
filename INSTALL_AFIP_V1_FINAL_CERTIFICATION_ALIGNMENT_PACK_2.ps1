param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_CERTIFICATION_ALIGNMENT_PACK_2_$Stamp"
$Files = @(
"afip\demo_execution_gateway\runtime.py",
"afip\final_integration\runtime.py",
"afip\final_integration\dashboard.py",
"afip\four_profile_operations\runtime.py",
"config\four_profile_demo.json",
"tools\validate_financial_naming.py",
"tests\test_afip_final_capital_tier_authority.py",
"tests\test_milestone_s_pack_5_5.py",
"tests\test_milestone_s_pack_7_1_position_ceiling_semantics.py",
"tests\test_milestone_s_pack_7_2_position_capacity_policy.py",
"tests\test_phase_u_pack_3_5_lot_authority.py",
"tests\test_afip_sequential_profile_router.py",
"tests\test_afip_v1_final_consolidation.py",
"tests\test_afip_v1_final_integration.py",
"tests\test_phase_u_pack_3_3_6_profile_execution_research_control.py",
"tests\test_milestone_s_pack_5_4_1.py",
"tests\test_phase_u_pack_3_3_8_position_sizing_authority.py",
"tests\test_milestone_s_pack_2.py"
)
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
foreach ($Rel in $Files) {
  $Source = Join-Path $PackRoot $Rel
  $Target = Join-Path $ProjectRoot $Rel
  if (!(Test-Path $Source)) { throw "Patch source missing: $Rel" }
  if (Test-Path $Target) {
    $Backup = Join-Path $BackupRoot $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
    Copy-Item -Force $Target $Backup
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $Source $Target
  Write-Host "Installed: $Rel"
}
Write-Host "Backup: $BackupRoot"
Write-Host "Installation complete."

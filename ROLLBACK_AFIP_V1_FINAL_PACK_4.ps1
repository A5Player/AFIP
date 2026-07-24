param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$Marker = Join-Path $ProjectRoot "backup\AFIP_V1_FINAL_PACK_4_LAST_BACKUP.txt"
if (!(Test-Path $Marker)) { throw "Pack 4 backup marker not found." }
$Backup = (Get-Content $Marker -Raw).Trim()
if (!(Test-Path $Backup)) { throw "Backup directory not found: $Backup" }
Get-ChildItem -Path $Backup -Recurse -File | ForEach-Object {
  $Rel = $_.FullName.Substring($Backup.Length).TrimStart('\')
  $Target = Join-Path $ProjectRoot $Rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
  Copy-Item -Force $_.FullName $Target
  Write-Host "Restored: $Rel"
}
Write-Host "Pack 4 rollback complete from $Backup"

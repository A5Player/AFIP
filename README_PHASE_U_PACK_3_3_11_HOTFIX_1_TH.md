# AFIP Phase U Pack 3.3.11 Hotfix 1

แก้ไขสองจุด:

1. เปลี่ยน marker ใน PowerShell เป็น ASCII เพื่อให้ Windows PowerShell อ่านสคริปต์ได้แน่นอน
2. เปลี่ยนคำศัพท์เกี่ยวกับการควบคุม Drawdown เป็น Drawdown Protection เพื่อผ่าน Financial Naming Validation

ไม่ต้องรัน APPLY_PHASE_U_PACK_3_3_11.ps1 ซ้ำ

รันตามลำดับ:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_11.ps1
```

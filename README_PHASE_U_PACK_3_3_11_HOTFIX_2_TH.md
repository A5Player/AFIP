# AFIP Phase U Pack 3.3.11 Hotfix 2

แก้เฉพาะเอกสาร Hotfix 1 ที่ยังมีคำศัพท์ไม่ผ่าน Financial Naming Validation

ไม่ต้องรันสคริปต์ Apply ซ้ำ เพราะ Runtime Git Isolation และ Documentation Update สำเร็จแล้ว

รันเฉพาะ:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_11.ps1
```

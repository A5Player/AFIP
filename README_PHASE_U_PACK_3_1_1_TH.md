# AFIP Phase U Pack 3.1.1

Renderer Compatibility Fix

แก้ ImportError:

`cannot import name 'SplitDashboardRenderer'`

โดยเพิ่ม `SplitDashboardRenderer` เป็นคลาสสืบทอดจาก `ThreeDashboardRuntime` เพื่อรักษา API ที่ Test และแพตช์ Pack 3.1 ใช้งาน โดยไม่ทำซ้ำ Rendering Logic

ขอบเขต:

- แก้เฉพาะ Dashboard renderer compatibility
- ไม่เปลี่ยน Trading Logic
- ไม่เปลี่ยน Lot, SL, TP หรือ Execution Authority

รัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_1_1.ps1
```

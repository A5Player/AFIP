# Phase U Pack 3 — Dashboard Runtime Finalization

## ขอบเขต
- เปลี่ยน `afip_dashboard.html` เป็นหน้า Home เชื่อม Dashboard 3 หน้า
- ไม่รัน Automatic Research แบบ synchronous โดยค่าเริ่มต้น
- ทำให้ `python -m afip.dashboard_ui` สร้างไฟล์แล้วคืน Prompt
- ไม่แก้ Trading Engine, Profile Policy, Position Sizing, SL/TP หรือ Execution Authority

## ติดตั้ง
1. แตก ZIP **ลงใน `C:\AFIP` โดยตรง** และเลือก Merge/Replace เมื่อ Windows ถาม
2. เปิด PowerShell
3. รัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process Bypass
.\INSTALL_PHASE_U_PACK_3_DASHBOARD_RUNTIME_FINALIZATION.ps1
.\RUN_PHASE_U_PACK_3_DASHBOARD_RUNTIME_FINALIZATION.ps1
```

## เปิด Dashboard
`C:\AFIP\runtime\dashboard\afip_dashboard.html`

## Research แบบตั้งใจ
```powershell
$env:AFIP_DASHBOARD_RUN_RESEARCH="YES"
python -m afip.dashboard_ui
Remove-Item Env:AFIP_DASHBOARD_RUN_RESEARCH
```

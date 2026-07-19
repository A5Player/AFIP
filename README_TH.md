# AFIP Phase U — Dashboard Home & Runtime Exit Fix

แพตช์เฉพาะจุดนี้แก้ 2 ปัญหา:

1. `afip_dashboard.html` เปลี่ยนเป็นหน้า Home เชื่อม Dashboard 3 หน้า
2. `python -m afip.dashboard_ui` ไม่รัน Automatic Research แบบเต็มโดยอัตโนมัติอีกต่อไป จึงสร้าง Dashboard และคืน PowerShell prompt ได้ตามปกติ

Automatic Research ยังไม่ได้ถูกลบ สามารถสั่งอย่างตั้งใจได้ด้วย:

```powershell
$env:AFIP_DASHBOARD_RUN_RESEARCH="YES"
python -m afip.dashboard_ui
Remove-Item Env:AFIP_DASHBOARD_RUN_RESEARCH
```

## ติดตั้ง

แตก ZIP ลงโฟลเดอร์ชั่วคราว แล้วเปิด PowerShell ที่ `C:\AFIP`:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& "<โฟลเดอร์แพตช์>\INSTALL_PHASE_U_DASHBOARD_HOME_RUNTIME_FIX.ps1"
.\RUN_PHASE_U_DASHBOARD_HOME_RUNTIME_FIX.ps1
```

แพตช์ไม่แก้ Trading Engine, Position Sizing, SL/TP, Profile Policy หรือ Execution Authority

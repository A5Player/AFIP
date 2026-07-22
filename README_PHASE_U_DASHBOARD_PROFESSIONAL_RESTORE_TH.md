# AFIP Dashboard Professional Restore

แก้ไข Dashboard ที่ถูกแทนด้วย JSON ดิบ โดยคืน Dashboard เดิมที่มีการ์ด ไอคอน ตาราง และรายละเอียดครบ แล้วเพิ่มหน้า 4 สำหรับ Data Loading & Research Operations แบบมืออาชีพ

## หน้า Dashboard
1. Operations — P1-P4
2. Intelligence & Engines
3. Research & Ranking
4. Data Loading & Research Operations

## ติดตั้ง
แตก ZIP ทับที่รากโปรเจ็กต์ จากนั้นรัน:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\CLEAN_BROKEN_DASHBOARD_HOTFIX.ps1
.\BUILD_AFIP_DASHBOARD_4_ONCE.ps1
```

สำหรับ Live Builder:

```powershell
.\START_AFIP_DASHBOARD_4_LIVE.ps1
```

Dashboard เป็น read-only และไม่เปลี่ยน execution authority.

# AFIP V1 Control Center Pack 1

Baseline: `f471f2c`

แพ็กนี้เพิ่มหน้า Control Center แบบอ่านสถานะเท่านั้น ผ่าน `DashboardAuthority` เดิม ไม่สร้าง execution gateway ใหม่ ไม่รัน research แบบ synchronous ระหว่าง build dashboard และไม่เปลี่ยน execution authority

## ติดตั้ง

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
cd C:\AFIP_V1_CONTROL_CENTER_PACK_1
.\INSTALL_AFIP_V1_CONTROL_CENTER_PACK_1.ps1 -ProjectRoot C:\AFIP\source
```

## ตรวจสอบ

```powershell
.\RUN_AFIP_V1_CONTROL_CENTER_PACK_1.ps1 -ProjectRoot C:\AFIP\source
```

## Full regression

```powershell
cd C:\AFIP\source
.\.venv\Scripts\python.exe -m pytest -q
```

หน้าที่สร้าง: `runtime/dashboard/afip_control_center.html`

Rollback ให้คัดลอกไฟล์จาก backup ตาม timestamp ใน `runtime/backups/control_center_pack_1/` กลับไปยัง relative path เดิม ห้ามลบ Repository, runtime data หรือ research data ทั้งชุด

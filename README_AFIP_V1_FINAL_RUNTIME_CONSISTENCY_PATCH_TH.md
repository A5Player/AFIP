# AFIP V1 Final Runtime Consistency Patch REV2

REV2 แก้ Windows path normalization ใน research file index ให้ใช้ `/` อย่างสม่ำเสมอ และรองรับ index เดิมที่บันทึกด้วย `\`.

ผลทดสอบ focused certification: `11 passed`.

## ติดตั้ง

```powershell
cd C:\AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH_REV2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH_REV2.ps1 -ProjectRoot C:\AFIP
```

## ทดสอบ

```powershell
.\RUN_AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH_REV2.ps1 -ProjectRoot C:\AFIP
```

# AFIP V1 Final Runtime Consistency Patch

ขอบเขตแพตช์นี้:

- เมื่อ Runtime process หยุดแล้ว Router state ต้องแสดง `STOPPED`
- Research Engine และ Runtime Observatory ไม่แสดง `RUNNING` จาก snapshot เก่า
- ล้าง stale PID/process_id ในสถานะที่นำไปแสดง
- STOP_AFIP บันทึก canonical stopped snapshots ลง source runtime state
- ไฟล์ runtime/status ที่ไม่ใช่ OHLC จะถูกจัดเป็น `NON_OHLC_SKIPPED`
- นับ rejected เฉพาะ record ที่มีลักษณะ OHLC แต่ข้อมูลไม่ถูกต้อง
- คง field `rejected_records` เดิมเพื่อ backward compatibility
- Research ไม่มี execution authority และไม่มี order send

## ติดตั้ง

```powershell
cd C:\AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH.ps1 -ProjectRoot C:\AFIP
```

## ทดสอบ

```powershell
cd C:\AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH
.\RUN_AFIP_V1_FINAL_RUNTIME_CONSISTENCY_PATCH.ps1 -ProjectRoot C:\AFIP
```

## ตรวจ lifecycle จริง

```powershell
cd C:\AFIP
.\.venv\Scripts\Activate.ps1
.\START_AFIP.ps1
.\STATUS_AFIP.ps1
.\STOP_AFIP.ps1
.\STATUS_AFIP.ps1
```

หลัง STOP ค่าหลักควรเป็น:

```text
status = STOPPED
trading_runtime.router.running = false
trading_runtime.router.state = STOPPED
research_runtime.process_state = STOPPED
research_runtime.engine.status = STOPPED
research_runtime.observatory.status = STOPPED
dashboard.process_state = STOPPED
dashboard.status.status = STOPPED
```

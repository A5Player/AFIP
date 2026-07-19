# AFIP Position Sizing Source Collection Pack

ชุดนี้ใช้ดึงเฉพาะไฟล์ Source ที่จำเป็นสำหรับแก้ Position Sizing Authority อย่างปลอดภัยจาก Repository ล่าสุดบนเครื่องคอม

## วิธีใช้

1. แตก ZIP นี้ลงที่ราก Repository เช่น `C:\AFIP`
2. เปิด PowerShell ที่ `C:\AFIP`
3. รัน:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\COLLECT_AFIP_POSITION_SIZING_SOURCE.ps1
```

หรือดับเบิลคลิก:

```text
COLLECT_AFIP_POSITION_SIZING_SOURCE.bat
```

ระบบจะสร้างไฟล์ประมาณ:

```text
AFIP_POSITION_SIZING_SOURCE_YYYYMMDD_HHMMSS.zip
```

ให้อัปโหลด ZIP ที่สร้างกลับมา แล้วจึงสามารถสร้าง Patch แบบไฟล์ทับได้ตรงกับ Source และ Commit ปัจจุบัน

ชุดนี้ไม่แก้ Runtime ไม่เปลี่ยน Config ไม่เปิด Execution และไม่แตะข้อมูลบัญชี

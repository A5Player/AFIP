# AFIP Phase U — Research Live Observability

Patch Only สำหรับเพิ่มการมองเห็นการทำงานของระบบวิจัย โดยไม่เปลี่ยน Trading Logic, Risk Policy หรือ Execution Authority

## สิ่งที่เพิ่ม

- Research Live Dashboard รีเฟรชทุก 10 วินาที
- แสดงสถานะรอบวิจัยและเวลาที่เขียนล่าสุด
- แสดงหลักฐาน Data Lake แยก M1, M5, M15, M30, H1, H4 และ D1
- แสดงจำนวนไฟล์ จำนวน records ที่ตรวจนับได้ ขนาดข้อมูล และ Last Write UTC
- แสดง Cross-market samples, sources และ evidence observations
- ใช้ `DATA_UNAVAILABLE` เมื่อยังไม่มีหลักฐานจริง ห้ามสร้างค่าจำลอง
- ยืนยัน `execution_authority=false` และ `order_send_called=false`

## ติดตั้ง

แตก ZIP ทับที่ `C:\AFIP\source` แล้วรัน:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pytest tests\test_phase_u_research_live_observability.py
.\BUILD_PHASE_U_RESEARCH_LIVE_DASHBOARD.ps1
```

เปิด:

`runtime\dashboard\afip_research_live_dashboard.html`

เมื่อ Continuous Research ทำงาน Dashboard จะถูกเขียนใหม่ก่อนและหลังแต่ละรอบ ส่วนหน้า HTML รีเฟรชทุก 10 วินาที

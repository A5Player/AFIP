# AFIP Phase U Dashboard Live Progress Hotfix

แพตช์นี้ปรับ Dashboard ก่อน โดยไม่เปลี่ยน Trading Policy หรือส่งคำสั่งซื้อขาย

- Dashboard เดียว 4 หน้า
- กดเลือกหน้าได้ และจำหน้าล่าสุด
- Build ซ้ำทุก 10 วินาที
- แสดง Stage, Heartbeat, M1-D1, Data Lake, Replay, Gap และไฟล์ที่กำลังเปลี่ยน
- ลบ HTML Dashboard เก่าเมื่อ Build
- เพิ่ม Heartbeat ต่อ Timeframe ใน AutomaticResearchRuntime สำหรับรอบถัดไป

## ระหว่าง Collector เดิมกำลังรัน
เปิด PowerShell ใหม่แล้วรัน:

```powershell
cd C:\AFIP\source
.\.venv\Scripts\Activate.ps1
.\START_AFIP_DASHBOARD_4_LIVE.ps1
```

อย่าทับไฟล์ Python ขณะ Collector เดิมทำงาน หากยังไม่ได้แตกแพตช์ ให้รอ Collector จบหรือหยุดก่อนติดตั้ง Overlay แต่สามารถ Build Dashboard จากไฟล์ที่ติดตั้งแล้วได้อย่างปลอดภัย

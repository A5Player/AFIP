AFIP V1 FINAL RUNTIME & DASHBOARD FIX

สิ่งที่แก้ในชุดเดียว
1. ยกเลิก Dashboard JSON fallback ที่เขียนทับหน้า Dashboard หลัก
2. ทุกคำสั่ง Dashboard ชี้ไป Single Dashboard Authority เดียว
3. Trading เริ่มโดยไม่รอ Historical Research, Replay, Dashboard หรือ Certification
4. Research ทำงานเป็น Background Process แยก
5. Dashboard Monitor ทำงานเป็น Background Process แยก และอัปเดตทุก 5 วินาที
6. หน้า Data Loading แสดงสถานะ, Current Stage, Timeframe, Heartbeat, จำนวน Bars,
   Replay Processed, Speed, ETA และ Progress Bar จากข้อมูลจริง
7. Financial Naming เปลี่ยนเป็น Fast Audit ไม่สแกนสำเนา Repository และไม่ขวางการเทรด
8. แก้ compatibility ของ Production Certification ที่ทำให้ Dashboard สร้างไม่ได้

วิธีติดตั้ง
- แตก ZIP ลงใน C:\AFIP\source
- เปิด PowerShell แบบปกติ
- รัน:

cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_RUNTIME_DASHBOARD_FIX.ps1

หลังติดตั้ง Dashboard จะเปิดอัตโนมัติ
ไฟล์หลัก: runtime\dashboard\afip_dashboard.html

ตรวจสถานะ:
.\STATUS_AFIP.ps1

หมายเหตุ
- Dashboard และ Research ไม่มีสิทธิ์ส่ง Order
- การโหลดข้อมูล/วิจัยไม่ขวาง Trading Runtime
- ห้ามใช้คำสั่งเก่าเพื่อสร้าง Dashboard ตัวอื่น ชุดนี้ทำให้คำสั่ง final integration
  ชี้กลับมาที่ Dashboard Authority เดียวแล้ว

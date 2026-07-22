# AFIP V1 Final Revision 1 — Compatibility Certification

แพตช์รับรองความเข้ากันได้ชุดสุดท้ายสำหรับ AFIP V1 Runtime Observatory

## ขอบเขต

- คืน field compatibility `margin_free` และ `profit` โดยยังรักษา field หลัก `free_margin` และ `floating_profit`
- รองรับ Dashboard spread contract เดิมทั้งสองรูปแบบที่ regression ปัจจุบันใช้งาน
- เพิ่ม metadata ยืนยัน Dashboard 4 เป็น Research Only:
  - `execution_authority=false`
  - `order_send_called=false`
- ลบการแสดงผลนโยบายเก่า Capital / 0.01 และ tier ออกจาก Dashboard profile rows
- ไม่เปลี่ยน Lot Authority, Execution Authority, Profile Risk, Replay หรือการ arm live

## ความปลอดภัย

- Patch Only
- Backward Compatible
- Dashboard เป็น read-only
- Research ไม่มี execution authority
- Live execution จะไม่ arm อัตโนมัติ

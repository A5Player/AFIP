# Milestone Q Pack 8 — การกำกับการตรวจสอบ Market Intent

เพิ่มชั้นกำกับแบบ deterministic และ immutable สำหรับหลักฐานการปรับเทียบความเชื่อมั่น Market Intent จาก Pack 7 ที่ผ่านแล้ว

## ขอบเขต
- ตรวจสอบ lineage ของ Pack 7 และรหัส calibration ที่ไม่ซ้ำ
- บังคับลำดับเวลา ความเชื่อมั่น coverage คุณภาพข้อมูล และเงื่อนไขก่อนหน้า
- สร้าง governance score, governance band, สถานะยอมรับ และความจำเป็นต้อง review
- เป็น research-only ไม่มีสิทธิ์ adaptive, production, broker, position หรือ execution

## การล็อกถาวร
- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base unit: 0.01 lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct execution: ปิด
- Order status: NO_ORDER_SENT

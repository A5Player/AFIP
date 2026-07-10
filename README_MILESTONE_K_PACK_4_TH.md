# Milestone K Pack 4 — Dynamic Stop Loss Intelligence

เพิ่มระบบทบทวน Stop Loss แบบ deterministic และอธิบายได้ สำหรับ XM GOLD# ใน Paper/Demo เท่านั้น

## การควบคุม
- ตรวจโครงสร้าง Stop Loss สำหรับ BUY/SELL
- การเลื่อนต้องลดระยะความเสี่ยง
- ต้องมีสถานะเปิด ความเสี่ยงผ่าน เวลาเหมาะสม และโครงสร้างตลาดยืนยัน
- คงหลัก 1 Unit = 0.01 Lot
- ไม่ส่งหรือแก้ไขคำสั่งจริง

## การตรวจสอบ
รัน `RUN_MILESTONE_K_PACK_4.ps1` หรือ `RUN_MILESTONE_K_PACK_4.bat`

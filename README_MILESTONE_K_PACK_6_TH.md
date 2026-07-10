# AFIP Milestone K Pack 6 — ระบบวิเคราะห์ Trailing Stop

## วัตถุประสงค์
เพิ่มการทบทวน Trailing Stop แบบ deterministic สำหรับ Paper/Demo Simulation โดยตรวจความพร้อม Break-even การล็อกกำไร Trailing หลายระยะ ความถูกต้องของ Stop สำหรับ BUY/SELL ต้นทุน ความเสี่ยง เวลา และโครงสร้างตลาด

## นโยบายความปลอดภัย
- โบรกเกอร์: XM เท่านั้น
- สัญลักษณ์: GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- โหมด: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: ปิดใช้งาน
- สถานะคำสั่ง: NO_ORDER_SENT

## ผลลัพธ์หลัก
ระบบแสดง Stop Loss ปัจจุบันและที่เสนอ กำไรล็อกขั้นต่ำและที่คาดว่าจะล็อก ระยะ Trailing เหตุผลการถือ เหตุผลการเลื่อน Trailing Stop การดำเนินการถัดไป Confidence และเวลาทบทวนถัดไป พร้อมคำอธิบายภาษาอังกฤษและไทยบน Dashboard

## การตรวจสอบ
รัน `RUN_MILESTONE_K_PACK_6.ps1` หรือ `RUN_MILESTONE_K_PACK_6.bat` จากโฟลเดอร์หลักของ repository

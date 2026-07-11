# AFIP Milestone Q Pack 5 — การยืนยันความเสถียรของ Market Intent

## วัตถุประสงค์

ตรวจสอบว่าสถิติ Market Intent จาก Pack 4 ที่ผ่านเกณฑ์มีความเสถียรต่อเนื่องข้ามช่วงข้อมูลวิจัยที่เรียงตามเวลาอย่างเคร่งครัดหรือไม่

## ไฟล์ที่เพิ่ม

- `afip/market_intent_stability_validation/__init__.py`
- `afip/market_intent_stability_validation/runtime.py`
- `tests/test_milestone_q_pack_5.py`
- `RUN_MILESTONE_Q_PACK_5.ps1`
- `RUN_MILESTONE_Q_PACK_5.bat`

## ขอบเขตการตรวจสอบ

Runtime ตรวจ lineage จาก Pack 4, identifier ไม่ซ้ำ, ลำดับเวลาไม่ทับซ้อน, ความครอบคลุมทางสถิติ, ช่วงค่าตัวชี้วัด, ช่วง persistence และ intensity, ช่วงอัตราการเปลี่ยนแปลง, ความสอดคล้องของ dominant pattern, stable-window ratio, คุณภาพข้อมูล, future safety, ลำดับเงื่อนไขก่อนหน้า และนโยบายล็อก Version 1.0

ผลลัพธ์เป็น deterministic, immutable และใช้เพื่อการวิจัยเท่านั้น ไม่สามารถปรับพารามิเตอร์ เปลี่ยนตรรกะการเทรด เลื่อนเป็น production knowledge แก้ไข position สร้าง broker request หรือส่งคำสั่งซื้อขาย

Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY`; live execution ถูกปิด; order status ยังคงเป็น `NO_ORDER_SENT`

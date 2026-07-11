# AFIP Milestone Q Pack 7 — การปรับเทียบความเชื่อมั่นของ Market Intent

## วัตถุประสงค์

ปรับเทียบความเชื่อมั่นเชิงวิจัยแบบ deterministic จากรายงาน Market Intent Drift ของ Pack 6 ที่ผ่านการยอมรับแล้ว

## ไฟล์ที่เพิ่ม

- `afip/market_intent_confidence_calibration/__init__.py`
- `afip/market_intent_confidence_calibration/runtime.py`
- `tests/test_milestone_q_pack_7.py`
- `RUN_MILESTONE_Q_PACK_7.ps1`
- `RUN_MILESTONE_Q_PACK_7.bat`

## ขอบเขตการปรับเทียบ

Runtime ตรวจสอบ lineage ของ Pack 6, drift ID ที่ไม่ซ้ำ, ลำดับเวลา, สถานะการยอมรับ drift, ค่าตัวชี้วัดที่เป็น finite และอยู่ในขอบเขต, คุณภาพข้อมูล, future safety, ลำดับ Market Regime และ Market Behaviour ก่อน Intent, ปริมาณหลักฐานขั้นต่ำ, ระดับความเชื่อมั่นขั้นต่ำ และนโยบายล็อก Version 1.0

ผลลัพธ์ประกอบด้วย raw drift confidence, evidence coverage, persistence consistency, intensity consistency, stability consistency, pattern consistency, calibrated confidence และระดับ `HIGH`, `MODERATE`, `CAUTIOUS` หรือ `INSUFFICIENT`

ผลลัพธ์เป็น immutable และใช้เพื่อการวิจัยเท่านั้น ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน trading logic เลื่อน knowledge เป็น production แก้ไข position สร้าง broker request ส่งคำสั่งซื้อขาย หรืออนุมัติ Production Certification

Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY`; live execution ปิดอยู่ และ order status ยังคงเป็น `NO_ORDER_SENT`

# AFIP Milestone Q Pack 6 — การตรวจจับ Market Intent Drift

## วัตถุประสงค์

ตรวจจับการเปลี่ยนแปลงของ Market Intent แบบ deterministic จากรายงาน Stability Validation ของ Pack 5 ที่ผ่านการยอมรับแล้ว

## ไฟล์ที่เพิ่ม

- `afip/market_intent_drift_detection/__init__.py`
- `afip/market_intent_drift_detection/runtime.py`
- `tests/test_milestone_q_pack_6.py`
- `RUN_MILESTONE_Q_PACK_6.ps1`
- `RUN_MILESTONE_Q_PACK_6.bat`

## ขอบเขตการตรวจจับ

Runtime ตรวจสอบ lineage ของ Pack 5, รหัสที่ไม่ซ้ำ, ลำดับเวลาที่ไม่ทับซ้อน, ช่วงค่าตัวชี้วัด, คุณภาพข้อมูล, future safety, ลำดับ Market Regime/Market Behaviour ก่อน Intent และนโยบายล็อก Version 1.0 พร้อมวัดการเปลี่ยนแปลงของ persistence, intensity, stability score, stable-window ratio และ dominant-pattern consistency รวมถึงการเปลี่ยนแปลงสูงสุดระหว่างช่วงที่ติดกัน

ผลลัพธ์ให้ drift score และระดับ `NONE`, `LOW`, `MODERATE` หรือ `HIGH` ระดับ Moderate/High ต้องได้รับการทบทวนเชิงวิจัยเท่านั้น และไม่มีสิทธิ์เปลี่ยนพารามิเตอร์หรือกฎการเทรด

Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY`, ปิด Live Execution และคงสถานะ `NO_ORDER_SENT`

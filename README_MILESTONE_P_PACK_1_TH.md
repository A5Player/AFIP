# AFIP Milestone P Pack 1 — Market Behaviour Intelligence Foundation

## วัตถุประสงค์

Patch นี้สร้างฐาน Market Behaviour Intelligence แบบ immutable และ deterministic สำหรับงานวิจัย โดยแปลงค่าตลาดที่ผ่านการรับรองเป็น Behaviour Observation หลังจากประเมิน Market Regime ก่อนแล้วเท่านั้น

## Behaviour State

- DIRECTIONAL_PERSISTENCE
- RANGE_ROTATION
- REGIME_TRANSITION
- VOLATILITY_EXPANSION
- VOLATILITY_COMPRESSION
- BALANCED_BEHAVIOUR

## การควบคุมความปลอดภัย

ระบบจะระงับ Observation เมื่อ Data Quality, ลำดับเวลา, Future Safety, ลำดับ Market Regime ก่อน Behaviour, ช่วงค่าตัวชี้วัด, นโยบาย XM/GOLD#/0.01 หรือ Execution Policy ไม่ผ่าน

Runtime นี้ไม่มีสิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อนข้อมูลเป็น Production Knowledge, แก้ Position, ติดต่อ Broker หรือส่ง Order

## ผลตรวจ

- Targeted tests: 8 passed
- Full test suite: 1503 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS

## การติดตั้ง

แตกไฟล์ Patch ทับที่ root ของ AFIP repository เท่านั้น ห้ามแทนที่ทั้ง repository และห้ามลบไฟล์ที่ไม่เกี่ยวข้อง

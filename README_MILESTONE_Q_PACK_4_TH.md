# AFIP Milestone Q Pack 4 — สถิติ Market Intent

## วัตถุประสงค์
เพิ่มชั้นสรุปสถิติแบบ deterministic และ immutable สำหรับรายงาน Market Intent Sequence ที่ผ่านเกณฑ์จาก Milestone Q Pack 3

## ขอบเขต
- ตรวจ lineage ของ Pack 3, รหัสไม่ซ้ำ, ลำดับเวลา และความสัมพันธ์ของจำนวนข้อมูล
- สรุปจำนวน observation และ transition
- คำนวณ weighted persistence และ weighted average intent intensity
- คำนวณอัตราการเปลี่ยน Intent, Direction, Market Regime และ Market Behaviour
- คำนวณค่าเฉลี่ยการเปลี่ยน intensity, continuation/reversal balance และ population standard deviation
- สร้าง distribution ของรูปแบบ sequence และ dominant pattern แบบ deterministic

## ความปลอดภัย
แพ็กนี้ใช้สำหรับงานวิจัยเท่านั้น ไม่สามารถปรับ parameter เปลี่ยน trading logic ติดต่อ broker แก้ไข position หรือส่ง order ได้ Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## การตรวจสอบ
```powershell
pytest tests/test_milestone_q_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

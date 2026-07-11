# AFIP Milestone Q Pack 3 — การวิเคราะห์ลำดับ Market Intent

## วัตถุประสงค์
เพิ่มการวิเคราะห์ Market Intent State ตามลำดับเวลาแบบ deterministic และ immutable โดยรับข้อมูลมาตรฐานจาก Milestone Q Pack 2

## ขอบเขต
- ตรวจสอบ lineage และ canonical schema ของ Pack 2
- บังคับลำดับเวลาให้เพิ่มขึ้นอย่างเคร่งครัด และห้าม state identifier ซ้ำ
- วัดการเปลี่ยนแปลงของ Intent, Direction, Market Regime และ Market Behaviour
- คำนวณ persistence, ค่าเฉลี่ย intensity, การเปลี่ยนแปลง intensity และการเปลี่ยนแปลง continuation/reversal balance
- จำแนกลำดับแบบ persistent, reversal, breakout development, liquidity seeking, oscillating หรือ mixed

## ความปลอดภัย
แพ็กนี้ใช้เพื่อการวิจัยเท่านั้น ไม่สามารถปรับพารามิเตอร์ เปลี่ยน trading logic ติดต่อ broker แก้ไข position หรือส่งคำสั่งซื้อขาย Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## การตรวจสอบ
```powershell
pytest tests/test_milestone_q_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

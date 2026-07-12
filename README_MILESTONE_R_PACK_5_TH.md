# Milestone R Pack 5 — Production Repository Cleanup

## วัตถุประสงค์

เพิ่มการกำกับ Repository Cleanup แบบ deterministic หลังผ่าน Regression Audit, Duplicate Code Audit, Dead Code Audit และ Architecture Audit

## ขอบเขต

- ตรวจ lineage จาก Milestone R Pack 4 Architecture Audit
- บันทึก cleanup action ที่ผ่านการทบทวนในรูปแบบ immutable
- อนุญาตเฉพาะรายการที่ไม่ใช่ protected source เช่น cache, generated artifact, เอกสารเก่า และ test artifact ที่หมดอายุ
- เก็บรักษา compatibility หรือ policy artifact ที่จำเป็นอย่างชัดเจน
- บล็อก action ที่ไม่ครบ, chronology ผิด, ID ซ้ำ, ความพยายามแตะ protected source และการละเมิด frozen policy
- ไม่เปลี่ยน trading logic, dependency wiring, execution หรือสถานะ Production Certification

## Execution Policy

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base unit: 0.01 lot
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: ปิด
- Live execution: ปิด
- Order status: `NO_ORDER_SENT`

## Validation

```powershell
pytest tests/test_milestone_r_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## งานถัดไป

Milestone R Pack 6 — Safety Audit

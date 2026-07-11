# AFIP Milestone O Pack 8 — Learning Validation Governance

## วัตถุประสงค์

Patch นี้เพิ่มการตรวจ Governance แบบ deterministic และ research-only ต่อจาก Milestone O Pack 7 Learning Confidence Calibration

## ขอบเขต

Runtime จะ:

- รับเฉพาะผล Calibration จาก Pack 7 ที่เป็น READY และผ่านการรับรอง;
- ตรวจ unique lineage, chronology, data quality และ future safety;
- บังคับใช้ความถูกต้องของ Feature Freeze policy version;
- บังคับแยกหน้าที่ Research Review ออกจาก Production Certification;
- ตรวจจำนวน Calibration, sample coverage และ confidence threshold ขั้นต่ำ;
- สร้างผล Governance แบบ immutable สำหรับการทบทวนด้วยมนุษย์ที่มีเอกสารรองรับ

## ความปลอดภัย

Runtime ไม่มีสิทธิ์:

- ปรับ Parameter อัตโนมัติ;
- เปลี่ยน Trading Logic;
- เลื่อนข้อมูลเป็น Production Knowledge;
- แก้ไข Position;
- สร้าง Broker Request;
- ส่งคำสั่งซื้อขาย

Execution ยังคง `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## การตรวจสอบ

```powershell
pytest tests/test_milestone_o_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

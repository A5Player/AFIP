# AFIP Milestone O Pack 7 — Learning Confidence Calibration

## วัตถุประสงค์

Patch นี้เพิ่มการปรับเทียบความเชื่อมั่นเชิงวิจัยแบบ Deterministic ต่อจาก Milestone O Pack 6 Learning Drift Detection

## ขอบเขต

Runtime จะ:

- รับเฉพาะรายงาน Pack 6 ที่มีสถานะ READY และไม่พบ Drift;
- ตรวจ Unique Lineage, ลำดับเวลา, คุณภาพข้อมูล และ Future Safety;
- ตรวจจำนวนรายงานและจำนวน Sample ขั้นต่ำ;
- รวม Raw Confidence, Evidence Coverage, ความเสถียรของ Realized-R Drift, Generalization และ Positive-window;
- สร้าง Calibrated Confidence Score และ Confidence Band;
- ระงับหลักฐานที่ไม่เพียงพอหรือไม่ผ่านเกณฑ์

## ความปลอดภัย

Runtime ไม่มีสิทธิ์:

- ปรับ Parameter อัตโนมัติ;
- เปลี่ยน Trading Logic;
- เลื่อนข้อมูลเป็น Production Knowledge;
- แก้ไข Position;
- สร้าง Broker Request;
- ส่ง Order

Execution ยังคง `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## การตรวจสอบ

```powershell
pytest tests/test_milestone_o_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

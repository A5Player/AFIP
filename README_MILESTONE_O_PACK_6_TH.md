# AFIP Milestone O Pack 6 — Learning Drift Detection

ตรวจจับ Drift ของข้อมูลการเรียนรู้แบบ deterministic และ research-only หลัง Pack 5 Learning Stability Validation

## ขอบเขต
- เปรียบเทียบช่วง Baseline กับช่วง Recent ที่ผ่านการรับรอง
- ตรวจ Drift ของค่าเฉลี่ย Evaluation Realized R
- ตรวจ Drift ของค่าเฉลี่ย Generalization Gap
- ตรวจ Drift ของ Positive Evaluation-window Rate
- ตรวจ Pack 5 lineage, ลำดับเวลา, จำนวนตัวอย่าง, คุณภาพข้อมูล, Future Safety และนโยบายล็อก

## ความปลอดภัย
Pack นี้ไม่มีสิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อนเป็น Production Knowledge, แก้ Position, สร้าง Broker Request หรือส่ง Order

Execution ยังคง `LOCKED_SIMULATION_ONLY`, Direct Execution = false, Live Execution = disabled และ Order Status = `NO_ORDER_SENT`

## คำสั่งตรวจ
```powershell
pytest tests/test_milestone_o_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

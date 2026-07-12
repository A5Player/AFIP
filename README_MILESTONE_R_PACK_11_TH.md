# Milestone R Pack 11 — การเตรียม Release Candidate

แพตช์นี้เพิ่มชั้นเตรียม Release Candidate แบบ deterministic และ immutable

ระบบต้องได้รับ Production Certification จาก Milestone R Pack 10 ที่ถูกต้อง พร้อมรายการไฟล์ รายการ validation และเอกสารภาษาอังกฤษ/ไทยครบถ้วน การผ่าน Pack นี้หมายถึง repository พร้อมเข้าสู่การทบทวน Release Candidate เท่านั้น ยังไม่ให้สถานะ Release Candidate หรือ Version 1.0 Final และยังไม่ปลดล็อก execution

นโยบายถาวรยังคงเดิม: XM เท่านั้น, GOLD# เท่านั้น, 1 Unit = 0.01 lot, `LOCKED_SIMULATION_ONLY`, ปิด direct execution, ปิด live execution และ `NO_ORDER_SENT`

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_r_pack_11.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

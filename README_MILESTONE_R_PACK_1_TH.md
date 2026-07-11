# AFIP Milestone R Pack 1 — Production Regression Audit

## วัตถุประสงค์

เพิ่มชั้นตรวจสอบ Regression แบบ deterministic และ immutable สำหรับขั้นแรกของ Milestone R Production Certification

## ขอบเขตการตรวจ

- Lineage จาก Milestone Q Pack 10
- จำนวน Full Test ก่อนหน้าและปัจจุบัน
- หลักฐาน Targeted Regression Test
- หลักฐาน Full pytest
- AFIP Local Quality Check
- Dashboard Build
- Financial Naming Validation
- MT5 Data Check
- ความไม่ซ้ำและลำดับเวลาของหลักฐาน
- นโยบายถาวร XM / GOLD# / 1 Unit = 0.01 Lot
- `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## ขอบเขตความปลอดภัย

ผล Regression Audit ที่ผ่านยังไม่ให้ Production Certification, Release Candidate, Direct Execution, Live Execution, การส่งคำขอไป Broker, การส่ง Order หรือการแก้ไข Position

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_r_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## งานถัดไป

Milestone R Pack 2 — Duplicate Code Audit

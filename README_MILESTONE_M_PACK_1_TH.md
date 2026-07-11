# AFIP Milestone M Pack 1 — Knowledge Intelligence Foundation

สร้างรากฐานระเบียนความรู้สำหรับการวิจัยที่เป็น Deterministic มีเวอร์ชันและมีคำอธิบาย หลัง Milestone L เสร็จสมบูรณ์

## ขอบเขต
- ตรวจลำดับเวลา รหัสไม่ซ้ำ Market Regime, Feature/Outcome Schema, Source Lineage, Explainability, คุณภาพข้อมูล และ Future Leakage
- อนุมัติเฉพาะ Research Knowledge
- ยังไม่เปิด Pattern Search, Clustering, Production Knowledge, Broker Request หรือ Order Transmission
- คงนโยบาย XM Only, GOLD# Only, 1 Unit = 0.01 Lot และ LOCKED_SIMULATION_ONLY

## การตรวจสอบ
```powershell
pytest tests/test_milestone_m_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

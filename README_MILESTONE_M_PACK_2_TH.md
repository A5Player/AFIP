# AFIP Milestone M Pack 2 — Pattern Knowledge Engine

สร้างกลไก Pattern Knowledge สำหรับการวิจัยจาก Knowledge Record ที่ผ่านการรับรองแล้วแบบ Deterministic

## ขอบเขต
- ต้องผ่าน Knowledge Intelligence Foundation จาก Milestone M Pack 1
- ปรับ Feature Vector ให้เป็นรูปแบบมาตรฐานและสร้าง Pattern ID ที่คงที่
- แบ่ง Pattern ตาม Market Regime ก่อนการวิเคราะห์
- รวม Pattern ที่ซ้ำกันโดยไม่สร้างระเบียนความรู้ซ้ำ
- บันทึกผล Accepted/Rejected และค่า R-Multiple
- รักษา Source Lineage, Data Quality Certification และการป้องกัน Future Leakage
- เปิดเฉพาะ Pattern Statistics และ Pattern Validation
- ยังไม่เปิด Similarity Search, Clustering, Production Knowledge Approval, Broker Request หรือ Order Transmission
- คงนโยบาย XM Only, GOLD# Only, 1 Unit = 0.01 Lot และ LOCKED_SIMULATION_ONLY

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_m_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

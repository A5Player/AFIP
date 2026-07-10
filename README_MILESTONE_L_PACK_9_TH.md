# AFIP Milestone L Pack 9 — Production Release Candidate

## วัตถุประสงค์
รวมความพร้อมจาก Milestone L Pack 1-8 และระบบควบคุมที่จำเป็นของ Version 1.0 เพื่อสร้างเกณฑ์ Production Release Candidate แบบ Deterministic

## ขอบเขต
- ตรวจ Dependency ของ Pack 1-8
- ตรวจ Lineage จาก Demo Execution Certification
- ตรวจ Production Health Monitor
- ตรวจ Emergency Safety System
- ตรวจ Production Report และ Decision Ledger
- ตรวจ Data Quality Certification
- ตรวจ Knowledge Versioning และ Feature Flags
- ตรวจคู่มือการใช้งานภาษาอังกฤษและภาษาไทย
- ตรวจ Audit Chain
- บังคับใช้ Independent Trade Plan
- รวม Protected Runner ใน Portfolio Exposure
- ห้าม Traditional DCA และ Averaging Down
- สร้าง Release Candidate ID แบบ Deterministic
- แสดงผลบน Dashboard ภาษาอังกฤษและภาษาไทย

## ขอบเขตการรับรอง
ผล READY หมายถึง `release_candidate_approved=True` เท่านั้น ยังไม่ถือว่าผ่าน Production Certification และ `production_certified` ยังคงเป็น False จนกว่า Milestone L Pack 10 และกระบวนการรับรอง Version 1.0 ทั้งหมดจะผ่าน

## นโยบายความปลอดภัย
- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: ปิด
- Order Status: NO_ORDER_SENT
- Broker Request Created: False
- Order Transmission Attempted: False

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

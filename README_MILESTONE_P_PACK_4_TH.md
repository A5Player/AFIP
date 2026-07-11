# AFIP Milestone P Pack 4 — สถิติการเปลี่ยนผ่านพฤติกรรมตลาด

แพตช์นี้รวมรายงานลำดับพฤติกรรมตลาดจาก Pack 3 ที่ผ่านการรับรองให้เป็นสถิติงานวิจัยแบบ immutable และ deterministic

## ขอบเขต

- ความถี่ของการเปลี่ยนผ่าน
- อัตราความต่อเนื่องแบบถ่วงน้ำหนัก
- อัตราการเปลี่ยน Regime, Behaviour และ Direction
- Regime และ Behaviour หลัก
- ตรวจ lineage และข้อมูลซ้ำจาก Pack 3
- ตรวจลำดับเวลา คุณภาพข้อมูล และ future safety
- ตรวจ Feature Freeze และ Execution Lock ถาวร

ส่วนนี้ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน Trading Logic เลื่อนข้อมูลเป็น Production Knowledge แก้ไข Position สร้างคำขอ Broker หรือส่งคำสั่งซื้อขาย

## คำสั่งตรวจ

```powershell
pytest tests/test_milestone_p_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

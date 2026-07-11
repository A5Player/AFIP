# AFIP Milestone O Pack 3 — Learning Evidence Aggregation

Patch นี้รวม Evidence ที่ผ่าน Milestone O Pack 2 ให้เป็นสถิติวิจัยแบบ deterministic ตรวจสอบย้อนหลังได้ และแยก Dataset Role อย่างชัดเจน พร้อมตรวจ Evidence ID ซ้ำ ลำดับเวลา Future Leakage คุณภาพข้อมูล ค่าตัวเลข Financial Label และนโยบาย Version 1.0 ที่ล็อกไว้

Patch นี้ไม่มีสิทธิ์ปรับ Parameter เปลี่ยน Trading Logic เลื่อนข้อมูลเป็น Production Knowledge แก้ Position สร้าง Broker Request หรือส่ง Order

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_o_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

# Milestone R Pack 3 — Production Dead Code Audit

เพิ่มชั้นตรวจสอบหลักฐาน dead code แบบ deterministic และ immutable

## ขอบเขต

- ต้องมี lineage ที่ถูกต้องจาก Milestone R Pack 2 Duplicate Code Audit
- จำแนก unreachable code, unused symbol, unused module, obsolete path และโค้ดที่ต้องเก็บไว้ตามนโยบาย
- ตรวจสอบ finding ID, SHA-256 fingerprint, ลำดับเวลา, สถานะการทบทวน, อัตรา dead code, ระดับความรุนแรง และนโยบาย execution ถาวร
- บันทึกรายการ cleanup ที่ต้องดำเนินการ โดยไม่ลบ source code และไม่เปลี่ยน runtime wiring

## ความปลอดภัย

Pack นี้ยังไม่ให้ Production Certification หรือ Release Candidate และไม่สามารถเปิด direct/live execution, สร้างคำขอไปยัง broker, แก้ไข position หรือส่ง order

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_r_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

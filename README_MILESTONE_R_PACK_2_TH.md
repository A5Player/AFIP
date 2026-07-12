# Milestone R Pack 2 — Production Duplicate Code Audit

เพิ่มชั้นตรวจสอบหลักฐานโค้ดซ้ำแบบ deterministic และ immutable ที่ผ่านการทบทวนแล้ว

Audit ตรวจสอบ lineage จาก Regression Audit Pack 1, รหัส finding, ลำดับเวลา, schema ของหลักฐาน, สถานะการทบทวน, อัตรา duplicate ที่ต้องดำเนินการ, ระดับความรุนแรง และนโยบาย trading/execution แบบถาวร

โค้ดซ้ำที่จำเป็นสามารถยอมรับได้เมื่อจัดประเภทและทบทวนอย่างชัดเจน ส่วนโค้ดซ้ำที่ต้องดำเนินการจะถูกบันทึกไว้สำหรับ cleanup แบบควบคุมใน Milestone R เท่านั้น Pack นี้ไม่ refactor และไม่ลบ source code

Production Certification, Release Candidate, direct execution, live execution, broker request, การแก้ไข position และการส่ง order ยังคงปิดทั้งหมด

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_r_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## งานถัดไป

Milestone R Pack 3 — Dead Code Audit

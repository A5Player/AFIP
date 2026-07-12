# Milestone R Pack 4 — การตรวจสอบสถาปัตยกรรมสำหรับ Production

เพิ่มชั้นตรวจสอบหลักฐานสถาปัตยกรรมแบบ deterministic และ immutable สำหรับ AFIP Version 1.0 Production Certification

## ขอบเขต
- ต้องมี lineage จาก Milestone R Pack 3 Dead Code Audit ที่ผ่านแล้ว
- ตรวจ module boundary, dependency direction, dependency cycle, public API, policy violation และ accepted exception
- ตรวจ finding ID, SHA-256 fingerprint, ลำดับเวลา, สถานะการทบทวน, architecture score, severity และนโยบาย execution ถาวร
- บันทึกสิ่งที่ต้อง cleanup โดยยังไม่ refactor ไม่เปลี่ยน dependency และไม่แก้ runtime wiring

## ความปลอดภัย
ยังไม่ให้ Production Certification หรือ Release Candidate ระบบยังเป็น `LOCKED_SIMULATION_ONLY` ปิด direct/live execution และคง `NO_ORDER_SENT`

## การตรวจสอบ
```powershell
pytest tests/test_milestone_r_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

งานถัดไป: Milestone R Pack 5 — Repository Cleanup

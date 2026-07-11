# AFIP Milestone O Pack 9 — Learning Review Certification

## วัตถุประสงค์
Patch นี้รับรองว่ารายงาน Governance ที่ผ่าน Milestone O Pack 8 ได้รับการทบทวนงานวิจัยด้วยมนุษย์และมีเอกสารครบถ้วน

## ขอบเขต
- ตรวจ Pack 8 lineage รูปแบบ `OGOV-`
- ตรวจลำดับเวลาและกำหนดให้เวลาทบทวนเกิดหลังหลักฐานทั้งหมด
- กำหนด Reviewer ที่ไม่ใช่ระบบอัตโนมัติ
- กำหนด Review record รูปแบบ `OREV-`, Review notes และผล `APPROVED_FOR_RESEARCH_CONTINUATION`
- ตรวจจำนวนรายงาน จำนวนตัวอย่าง Confidence คุณภาพข้อมูล Future Safety และนโยบาย Version 1.0 ที่ถูกล็อก
- สร้าง Certification ID รูปแบบ `OCERT-` แบบ deterministic

## ขอบเขตความปลอดภัย
การรับรองนี้อนุญาตเฉพาะการตรวจงานวิจัยต่อไปเท่านั้น ไม่อนุญาตให้ปรับ Parameter อัตโนมัติ เปลี่ยน Trading Logic เลื่อน Knowledge สู่ Production แก้ Position สร้างคำขอ Broker หรือส่งคำสั่งซื้อขาย

Execution ยังคง `LOCKED_SIMULATION_ONLY`, Direct Execution เป็น false, Live Execution ถูกปิด และสถานะคำสั่งคือ `NO_ORDER_SENT`

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_o_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone O Pack 9 Learning Review Certification"
git push
```

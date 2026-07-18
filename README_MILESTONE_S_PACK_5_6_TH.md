# AFIP Milestone S Pack 5.6 — ฐานข้อมูลวิจัย

แพตช์นี้สร้างสัญญาข้อมูลวิจัยแบบมีเวอร์ชันและระบบอ่านได้ โดยไม่เปลี่ยนโหมด Execution หรือพฤติกรรมการส่งคำสั่ง

## ขอบเขต

- Data Dictionary ฐานกลาง ไม่ผูกกับ P1-P4
- Score Dictionary แสดงองค์ประกอบ สูตร และ Hard Gate แยกจากคะแนน
- Formula Registry สำหรับตรวจสอบและคำนวณย้อนหลัง
- กฎคุณภาพข้อมูล
- กฎ Research Eligibility และ Quarantine
- Decision Trace Envelope
- คู่มือข้อมูลและคะแนน
- Regression Tests

## ความปลอดภัย

Pack นี้ไม่ปลดล็อก Demo/Live ไม่ลดเกณฑ์ ไม่ส่งออเดอร์ และกำหนดให้ Raw Data เป็นข้อมูล Append-only ที่ห้ามเขียนทับ

## การทดสอบ

```powershell
.\RUN_MILESTONE_S_PACK_5_6.ps1
python tools\afip_local_quality_check.py
```

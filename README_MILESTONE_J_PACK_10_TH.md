# Milestone J Pack 10 — การรับรอง Decision Intelligence

Patch แบบเพิ่มเฉพาะส่วนนี้ใช้ปิด Milestone J ด้วยชั้นรับรองแบบ deterministic และ read-only

## ขอบเขต

- รับรองตั้งแต่ Market Regime V2 ถึง Portfolio Decision Engine
- ตรวจนโยบาย Version 1: XM เท่านั้น และ GOLD# เท่านั้น
- ตรวจว่า 1 Unit เท่ากับ 0.01 lot เสมอ
- ตรวจว่า Direct Execution และ Live Execution ยังคงปิด
- เพิ่มสถานะการรับรองและการกระทำถัดไปบน Dashboard ทั้งภาษาอังกฤษและภาษาไทย
- ไม่เปิด แก้ไข หรือปิดคำสั่งซื้อขาย

## ลำดับติดตั้ง

ติดตั้งหลัง Milestone J Pack 9

## การตรวจสอบ

รัน `RUN_MILESTONE_J_PACK_10.ps1` หรือ `RUN_MILESTONE_J_PACK_10.bat`

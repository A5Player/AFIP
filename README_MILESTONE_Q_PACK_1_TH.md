# AFIP Milestone Q Pack 1 — รากฐาน Market Intent Intelligence

## วัตถุประสงค์

แพตช์นี้สร้างรากฐานงานวิจัยของ Market Intent Intelligence แบบ immutable และ deterministic โดยจะแปลงหลักฐาน Market Regime และ Market Behaviour ที่ผ่านการรับรองเป็น Market Intent Observation เฉพาะเมื่อประเมินเงื่อนไขทั้งสองตามลำดับก่อนแล้วเท่านั้น

## สถานะ Intent

- BUYING_PRESSURE — แรงกดดันฝั่งซื้อ
- SELLING_PRESSURE — แรงกดดันฝั่งขาย
- LIQUIDITY_SEEKING — พฤติกรรมค้นหาสภาพคล่อง
- BREAKOUT_ATTEMPT — ความพยายามทะลุกรอบ
- REVERSAL_ATTEMPT — ความพยายามกลับทิศ
- BALANCED_INTENT — Intent สมดุล

## การควบคุมความปลอดภัย

ระบบจะระงับ Observation เมื่อไม่ผ่านการตรวจคุณภาพข้อมูล ลำดับเวลา Future Safety ลำดับ Market Regime ลำดับ Market Behaviour ช่วงค่าตัวชี้วัด นโยบาย Broker/Symbol/Base Unit หรือนโยบายล็อกการส่งคำสั่ง

โมดูลนี้ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน Trading Logic เลื่อนข้อมูลเป็น Production Knowledge แก้ไข Position ติดต่อ Broker หรือส่ง Order

## การติดตั้ง

แตกไฟล์แพตช์ทับที่โฟลเดอร์รากของ AFIP ห้ามแทนที่ Repository ทั้งชุดและห้ามลบไฟล์ที่ไม่เกี่ยวข้อง

## การตรวจสอบ

รัน `RUN_MILESTONE_Q_PACK_1.ps1` หรือ `RUN_MILESTONE_Q_PACK_1.bat`

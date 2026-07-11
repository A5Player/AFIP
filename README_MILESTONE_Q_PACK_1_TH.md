# AFIP Milestone Q Pack 1 — รากฐาน Market Intent Intelligence

## วัตถุประสงค์

แพตช์นี้สร้างรากฐานงานวิจัยแบบ immutable และ deterministic สำหรับ Market Intent Intelligence โดยแปลงหลักฐาน Market Regime และ Market Behaviour ที่ผ่านการรับรองให้เป็น Intent Observation หลังจากประเมินทั้งสองส่วนตามลำดับที่กำหนดแล้วเท่านั้น

## สถานะ Intent

- BUYING_PRESSURE — แรงกดดันฝั่งซื้อ
- SELLING_PRESSURE — แรงกดดันฝั่งขาย
- LIQUIDITY_SEEKING — การเคลื่อนไหวเพื่อค้นหาสภาพคล่อง
- BREAKOUT_ATTEMPT — ความพยายามทะลุกรอบ
- REVERSAL_ATTEMPT — ความพยายามกลับทิศ
- BALANCED_INTENT — Intent สมดุล

## การควบคุมความปลอดภัย

Runtime จะระงับ Observation หากไม่ผ่านการตรวจคุณภาพข้อมูล ลำดับเวลา Future Safety ลำดับ Market Regime ลำดับ Market Behaviour ช่วงค่าตัวชี้วัด นโยบาย Broker/Symbol/Base Unit หรือนโยบาย Execution ที่ล็อกไว้

โมดูลนี้ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน Trading Logic เลื่อนความรู้เข้าสู่ Production แก้ไข Position ติดต่อ Broker หรือส่ง Order

## การติดตั้ง

แตกไฟล์ Patch ทับที่รากของ AFIP repository เท่านั้น ห้ามแทนที่ repository ทั้งชุดและห้ามลบไฟล์ที่ไม่เกี่ยวข้อง

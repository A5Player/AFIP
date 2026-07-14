# Milestone S Pack 4 — Demo Execution Gateway

AFIP สามารถส่งคำสั่ง `GOLD#` ที่มี SL/TP ได้ เฉพาะเมื่อ Gateway ตรวจยืนยันว่าบัญชี MT5 เป็น **บัญชี Demo** (`trade_mode=0`) เท่านั้น บัญชีจริงและบัญชี Contest จะถูกบล็อกก่อนถึง `order_send`

## นโยบายโปรไฟล์

- P1 High Safety: เงินทุน 1,000 USD ต่อ Unit 0.01 และ Confidence ขั้นต่ำ 98
- P2 Balanced: เงินทุน 500 USD ต่อ Unit 0.01 และ Confidence ขั้นต่ำ 95
- P3 High Risk Within Plan: เงินทุน 200 USD ต่อ Unit 0.01 และ Confidence ขั้นต่ำ 90
- P4 Research: เงินทุน 100 USD ต่อ Unit 0.01 และ Confidence ขั้นต่ำ 60
- สูงสุด 3 ออเดอร์แยก ออเดอร์ละ 0.01 ต่อโปรไฟล์

## ประตูความปลอดภัยบังคับ

XM เท่านั้น, `GOLD#` เท่านั้น, Account/Server ต้องตรง, ต้องเป็น Demo, ต้องอนุญาต Expert Trading, ห้ามใช้ข้อมูล Fallback, Risk และ Trading Cost ต้องผ่าน, ต้องมีแผน SL/TP, หากพบออเดอร์ Manual จะหยุด, ต้องเปิดสวิตช์ยืนยันสองชั้นเฉพาะเครื่อง, ต้องมี Unit Capacity และมี Duplicate Cooldown

สคริปต์ Validation จะไม่เปิดสวิตช์และไม่ส่งออเดอร์

# คู่มือ AFIP สำหรับเตรียมใช้งานจริง (ภาษาไทย)

## วัตถุประสงค์
AFIP คือระบบวิเคราะห์และตัดสินใจเชิงการเงินแบบ deterministic ที่เตรียมใช้งานจริงโดยเริ่มจาก simulation ก่อน ระบบต้องรักษาหลัก Market Regime before Signal Context และห้ามส่งคำสั่งจริงระหว่างที่ execution ยังล็อกเป็น simulation

## ลำดับการทำงานของ Runtime
1. อ่านข้อมูลตลาดจากแหล่งข้อมูลที่ตั้งค่าไว้
2. ประเมิน Market Regime ก่อนอ่าน Signal Context
3. ประเมิน market intelligence, risk intelligence, cost intelligence และ execution readiness
4. สร้างรายงานการตัดสินใจแบบ deterministic
5. บันทึก observability, event log, metrics, paper trading และ release candidate evidence

## การติดตั้ง
ใช้งานจาก root ของ repository บน Windows PowerShell ติดตั้ง requirements เชื่อมต่อ MT5 เมื่อจำเป็น และตรวจว่า `python afip.py mt5-check` แสดงสถานะ READY ก่อนทำ production review

## คำสั่งตรวจสอบ
ทุกครั้งก่อน commit ให้รัน pack test, full pytest และ local quality check คง execution เป็น simulation จนกว่าจะผ่านกระบวนการ live-readiness โดยตั้งใจ

## การกู้คืน
ถ้า production review ไม่ผ่าน ให้หยุด deployment คง execution เป็น simulation ตรวจ quality result และ rollback ไปยัง Git commit ล่าสุดที่ผ่านถ้าจำเป็น

## การแก้ปัญหา
ให้เริ่มจาก local quality check จากนั้นตรวจ simulation output, MT5 data check, feature flags, event log, runtime metrics และ production release candidate report

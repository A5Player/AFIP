# Production Bring-up Pack 6 — AFIP Bank Live

เพิ่มบัญชีเงินทุนแบบอ่านอย่างเดียวสำหรับ XM / GOLD# ในโหมด Paper และ Demo โดยแยกเงินฝากและเงินถอนภายนอกออกจากกำไรปิดแล้วและกำไรลอยตัว พร้อมแสดงยอดคงเหลือ Equity เงินสำรอง เงินที่จัดสรรได้ และผลตอบแทนสะสมบน Dashboard

## ความปลอดภัย
Live Execution ยังคงปิดอยู่ โมดูลนี้ไม่สามารถโอนเงิน ส่งคำสั่งซื้อขาย หรือแก้ไขการตัดสินใจเทรดได้ หาก Broker, Symbol, Mode หรือตัวเลขถอนเงินไม่ผ่านนโยบาย ระบบจะแสดง BLOCKED พร้อมเหตุผล

## ข้อมูลเข้า
`initial_capital`, `deposits`, `withdrawals`, `closed_profit`, `floating_profit`, `reserve` และ `bank_transactions` แบบเลือกใช้

## การทดสอบ
รัน `RUN_PRODUCTION_BRINGUP_PACK_6.ps1` หรือ `.bat`

# AFIP Milestone S Pack 4.2 — แก้สัญญา Trading Cost ของ Demo Execution

## ต้นเหตุที่ยืนยันแล้ว

`TradingCostIntelligence` กำหนดให้สถานะ `CAUTION` สามารถส่งคำสั่งได้เมื่อ `allowed=True` แต่ Demo Gateway เดิมยอมรับเฉพาะ `status == PASS` จึงบล็อก Spread ในช่วงเตือนก่อนถึง `order_check` และ `order_send`

## การแก้ไข

- Gateway ใช้ค่า `allowed` เป็นสัญญาหลัก
- `PASS` และ `CAUTION` ผ่านได้เฉพาะเมื่อ `allowed=True`
- `BLOCK` ยังถูกปิดกั้น
- สถานะไม่รู้จักหรือข้อมูลหายจะถูกปิดกั้นแบบ Fail Closed
- ไม่ลด Spread Threshold, Confidence Threshold, Position Sizing หรือ Safety Arm
- เพิ่มข้อมูล Spread, Threshold, Point, Digits และสถานะการเรียก MT5 ในรายงาน Gateway

## ผลทดสอบใน Repository ต้นทาง

- Pack regression: `13 passed`
- Pack + Dashboard regression: `15 passed`
- Full test suite: `1808 passed`

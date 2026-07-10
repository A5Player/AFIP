# Milestone J Pack 9 — กลไกตัดสินใจระดับพอร์ต

Patch แบบ incremental นี้รวม Entry Validation, Exit Validation, ความจุ Unit คงที่, Portfolio Exposure และการอนุมัติความเสี่ยงให้เป็นบริบทการตัดสินใจระดับพอร์ตที่อธิบายได้

## การตัดสินใจ

- ENTER
- HOLD
- PARTIAL_CLOSE
- MOVE_STOP_LOSS
- CHANGE_TAKE_PROFIT
- TRAIL_STOP
- EXIT
- WAIT

ระบบยังเป็นแบบอ่านอย่างเดียว ไม่ส่ง แก้ไข หรือปิดคำสั่งกับ Broker โดย Version 1 ยังคงใช้ XM และ GOLD# เท่านั้น และ 1 Unit เท่ากับ 0.01 lot เสมอ

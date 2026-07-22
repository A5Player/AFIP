# AFIP Phase U Pack 3.5
## รวม Lot และ Position Authority ล่าสุดเป็นศูนย์กลางเดียว

แพตช์นี้สร้าง Authority หลักแบบ deterministic และไม่มี side effect:
`afip.lot_authority.calculate_lot_authority`

สัญญาหลัก:
- 1 unit = 0.01 lot เสมอ
- สูงสุด 3 units ต่อ signal
- หลาย units ต้องเป็นหลายออเดอร์ 0.01 ห้ามรวมเป็น 0.02/0.03 ออเดอร์เดียว
- Approved units เป็นค่าต่ำสุดของ Requested, Confidence, Capital, Risk,
  Profile Max และ Execution Safety
- P3 ทุนต่ำกว่า 200 USD ยังอนุมัติ 1 × 0.01 ได้ เมื่อ balance/equity มากกว่า 0
- Demo Gateway ใช้ผลจาก Authority และไม่มีสิทธิ์เพิ่มจำนวนไม้
- Capital tiers เดิมยังเป็น input จาก config แต่ไม่ใช่ Authority แข่งขันกัน

ความปลอดภัย:
- ไม่เปิด execution อัตโนมัติ
- ไม่เปลี่ยน spread/trading-cost gate, SL/TP, Intelligence, broker policy,
  credentials หรือ runtime data ของผู้ใช้

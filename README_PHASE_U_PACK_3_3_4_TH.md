# AFIP Phase U Pack 3.3.4
## คุณภาพข้อมูลวิจัย M30 การตรวจช่องว่าง และ Automatic Backfill

แพตช์นี้เพิ่มหลักฐานคุณภาพข้อมูลแบบกำหนดผลลัพธ์ซ้ำได้ สำหรับ M1, M5, M15, M30, H1, H4 และ D1

สิ่งที่เพิ่ม:
- ตรวจความถูกต้องของ OHLC แยกตาม Timeframe Registry
- ตรวจ timestamp ซ้ำแบบตรงตัว
- ระบุช่วง Gap และจำนวนแท่งที่ขาดอย่างชัดเจน
- ตรวจ Freshness ตามระยะเวลาของแต่ละ Timeframe
- กลไกรับข้อมูล Backfill จาก Provider และรวมแบบไม่เขียนทับข้อมูลเดิม
- รองรับ MT5 Historical Gap Backfill สำหรับงานวิจัยเท่านั้น
- บันทึกแท่ง Backfill ที่ยอมรับแล้วลง Data Lake แบบ Append-only
- เพิ่มสถานะ Quality, Gap, Freshness และ Backfill ลง Automatic Research Status
- เชื่อม M30 เข้าสู่เส้นทาง Data Quality และ Backfill ครบถ้วน

ความปลอดภัย:
- ไม่เพิ่มสิทธิ์ส่งคำสั่งซื้อขาย
- ไม่เปลี่ยนนโยบาย Live Trading, Lot Size, Capital Gating, Maximum Units, SL หรือ TP
- ไม่เขียนทับข้อมูลย้อนหลังหรือข้อมูลวิจัยเดิม
- เมื่อรวมข้อมูล ข้อมูลเดิมมีสิทธิ์เหนือกว่าและข้อมูลซ้ำจะถูกข้าม

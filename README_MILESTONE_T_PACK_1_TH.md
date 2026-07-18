# AFIP Milestone T Pack 1
## ฐานระบบกักกันงานวิจัยและการเลื่อนข้อมูลเข้าสู่ Production

แพตช์นี้สร้างเขตแยกแบบ Fail Closed ระหว่างข้อมูลทดลองกับองค์ความรู้ที่ผ่านการอนุมัติแล้ว

## หลักประกันสำคัญ

- ข้อมูลทดลองแยกทางกายภาพและทางตรรกะจากข้อมูล Production
- Production อ่านได้เฉพาะข้อมูลสถานะ `PRODUCTION_APPROVED` ที่ตรวจสอบ Promotion Checksum แล้ว
- มีสถานะวงจรชีวิตชัดเจน: ทดลอง, รอตรวจ, ปฏิเสธ, ผู้สมัครที่ผ่าน, อนุมัติใช้งานจริง และเพิกถอน
- หลักฐานไม่ครบต้องถูกบล็อกเสมอ
- กำไรสูงหรือ Win Rate สูงไม่สามารถข้าม Drawdown, Out-of-Sample, Walk-Forward, Data Quality หรือ ระบบป้องกัน Future Leakage ได้
- ยกเลิกแนวคิด TOP10 และ TOP100
- ภายหลังระบบจะเลือกเฉพาะข้อมูลที่อนุมัติแล้ว โดยเปรียบเทียบตามบริบทตลาดปัจจุบันด้วย Drawdown ต่ำกว่า, กำไรสุทธิสูงกว่า และโอกาสชนะสูงกว่า
- Pack นี้ไม่เปลี่ยน Trading Logic, Profile, Lot Size, Position Sizing, TP, SL หรือสิทธิ์ส่งคำสั่ง

## เส้นทางการเลื่อนสถานะ

`EXPERIMENTAL -> VALIDATION_PENDING -> APPROVED_CANDIDATE -> PRODUCTION_APPROVED`

ข้อมูล `REJECTED` และ `REVOKED` ห้าม Production อ่าน

## เกณฑ์เริ่มต้น

- จำนวนตัวอย่างรวมอย่างน้อย 300 ออเดอร์
- Out-of-Sample อย่างน้อย 100 ออเดอร์
- Walk-Forward อย่างน้อย 3 ช่วง
- Profit Factor อย่างน้อย 1.20
- Expectancy ต้องเป็นบวก
- Maximum Drawdown ไม่เกิน 20%
- ยืนยัน Chronological Replay
- ไม่พบ Future Leakage
- ผ่าน Data Quality Certification
- ต้องมีการอนุมัติและระบุตัวผู้อนุมัติ

เกณฑ์อยู่ใน `config/research_promotion_policy.json` จึงแก้ไขได้โดยไม่ Hardcode ในระบบเปิดออเดอร์

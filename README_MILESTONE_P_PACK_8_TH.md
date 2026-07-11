# AFIP Milestone P Pack 8 — Market Behaviour Validation Governance

แพตช์นี้เพิ่ม Governance Gate แบบ Deterministic สำหรับผล Market Behaviour Confidence Calibration ที่ผ่าน Pack 7

## ขอบเขต

- ตรวจ Lineage และ `PBCF-` ID ที่ไม่ซ้ำจาก Pack 7
- ตรวจลำดับเวลาและป้องกัน Future Leakage
- บังคับ Market Regime before Market Behaviour
- ตรวจ Coverage และ Confidence threshold
- ตรวจ Version 1.0 Feature Freeze policy
- แยกหน้าที่ Research Review ออกจาก Production Certification
- กำหนดให้ Pack 9 ต้องมี Manual Review พร้อมเอกสาร
- รักษาการล็อก Adaptive, Production, Position, Broker และ Execution ทั้งหมด

## ความปลอดภัย

Runtime นี้ใช้เพื่อการวิจัยเท่านั้น ไม่มีสิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อน Production Knowledge, แก้ Position, สร้าง Broker Request หรือส่งคำสั่งซื้อขาย

## ผลตรวจ

- Targeted tests: 8 passed
- Full regression: 1559 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS

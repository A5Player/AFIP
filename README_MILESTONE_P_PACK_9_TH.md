# AFIP Milestone P Pack 9 — การรับรองการทบทวนพฤติกรรมตลาด

แพตช์นี้เพิ่มการรับรองแบบ deterministic ว่ารายงาน Market Behaviour Validation Governance จาก Pack 8 ได้รับการทบทวนด้วยมนุษย์และมีเอกสารครบถ้วน

## ขอบเขต

- ตรวจ lineage ของ `PBGV-` ไม่ให้ซ้ำและต้องถูกต้อง
- ต้องมีผู้ทบทวนที่เป็นมนุษย์และระบุตัวตนได้
- ต้องมีบันทึก `PBREV-` พร้อมหมายเหตุ
- เวลาทบทวนต้องเกิดหลังหลักฐาน Governance ทั้งหมด
- ผลทบทวนต้องเป็น `APPROVED_FOR_RESEARCH_CONTINUATION`
- ตรวจจำนวน Transition, Confidence, Data Quality, Future Safety และ Market Regime before Behaviour
- รักษา Feature Freeze และ Execution Lock ทั้งหมด

การรับรองนี้ใช้เพื่อการวิจัยเท่านั้น ไม่ได้ให้ Production Certification และไม่มีสิทธิ์ปรับ Parameter เปลี่ยน Trading Logic แก้ Position หรือส่งคำสั่งซื้อขาย

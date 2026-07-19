# AFIP Phase U Pack 3.3.7

## Final Integration, Regression & Pack Certification

แพ็กนี้ใช้ปิด Phase U Pack 3.3 อย่างเป็นทางการ โดยรับรองการเชื่อมต่อเส้นทางข้อมูลและงานวิจัย M30 รวมถึงการควบคุม Execution รายโปรไฟล์

ขอบเขตที่รับรอง:

- Timeframe Registry แบบ Data-driven ครบ M1, M5, M15, M30, H1, H4 และ D1
- MT5 Historical Collection และ Financial Data Lake แบบ append-only
- Chronological Replay แบบผูก exact source window และมีหลักฐาน checkpoint
- Gap Detection, Automatic Backfill, Freshness และ Data-quality validation
- Dashboard แสดง Coverage, Replay Progress, Freshness, Gap, Integrity และ Research Status
- Research Consumer ใช้ M30 ได้โดยไม่เปลี่ยน Live Trading Policy อัตโนมัติ
- P1/P4 เปิด Execution; P2/P3 ปิดเฉพาะ Execution แต่ยังรักษา Configuration, Historical Data และ Research Participation

แพ็กนี้ยังไม่รับรองความพร้อมบัญชีเงินจริง การรับรอง Lot sizing, Capital gating, Maximum units, SL, TP และ Real Execution Locks ต้องทำเป็นงานตรวจสอบแยกจากโค้ดและ Runtime จริง

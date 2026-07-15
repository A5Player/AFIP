# AFIP Milestone S Pack 5.1 — รากฐานข้อมูลวิจัย

เพิ่มระบบบันทึกข้อมูลวิจัยแบบอ่านอย่างเดียว มี Versioning และไม่เปลี่ยน Trading Logic หรือเส้นทางส่งคำสั่ง MT5

## ขอบเขต
- Data Contract `AFIP-RESEARCH-DATA-1.0`
- Decision/Gate และ Execution Events แบบ Append-only
- Trade Case File สำหรับออเดอร์ Demo ที่ส่งสำเร็จ
- เวลา UTC และ Data Lineage ด้วย SHA-256
- เตรียม Post-trade Checkpoint M30, H1, H4, D1
- นำเข้า Ledger ซ้ำได้โดยไม่สร้างข้อมูลซ้ำ
- แยกบรรทัดข้อมูลเสียไว้ใน Rejection Ledger
- ส่งออก JSON/JSONL เพื่อรองรับ AFIP Gold V2

## ความปลอดภัย
Recorder ไม่เชื่อม MT5 และไม่เรียก order_check, order_send, แก้ไข หรือปิด Position

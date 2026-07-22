# AFIP Phase U Pack 3.4.11 — Unified Continuous Historical Research & Dashboard 4

Patch Only สำหรับแก้ปัญหา Continuous เดิมที่รันเฉพาะ Cross-market Research และไม่ได้เรียก AutomaticResearchRuntime

วงจรใหม่:
1. โหลด Closed Bars จริงจาก MT5 สำหรับ Timeframe ที่ registry รองรับตั้งแต่ M1 ถึง D1
2. บันทึก Append-only Historical Data Lake
3. ตรวจ Gap และ Freshness พร้อม Backfill ที่มีหลักฐาน
4. รัน Chronological Replay แยกแต่ละ Timeframe
5. สร้าง Research Candidates และ Cross-market Evidence
6. เขียน Dashboard 4 สำหรับติดตามจำนวนแท่ง Coverage Gap และเวลาล่าสุด

ความปลอดภัย: Research only, execution_authority=false, order_send_called=false

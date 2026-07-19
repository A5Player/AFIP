# AFIP Milestone T Pack 9

## MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring และ Dashboard Data Contract Foundation

Pack นี้เพิ่มฐานเชื่อมข้อมูลย้อนหลัง MT5 แบบ Dependency Injection โดยไม่เพิ่มการส่งออเดอร์

### ขอบเขต
- แปลงชื่อสัญลักษณ์กลางให้ตรงกับชื่อ Broker เช่น GOLD#, XAUUSD, USOIL
- ดึงข้อมูลตั้งแต่เก่าสุดที่หาได้ถึงแท่งปิดล่าสุด
- แบ่งโหลดเป็นชุดและ Resume ต่อจาก Checkpoint ได้
- เก็บ Historical Bars และผลการโหลดแบบ Append-only
- บันทึกมาตรฐานวิจัยที่มีผลต่อการตัดสินใจแต่ละครั้ง
- กำหนด Data Contract ของ Dashboard สองหน้า
- จัดอันดับ Top 10 และกางดู Top 100 แยก Pattern/สถานการณ์

### Dashboard
1. หน้า Operations: P1-P4 อยู่หน้าเดียว รีเฟรชทุก 5 วินาที แสดงแผน มาตรฐาน Win Rate Drawdown Profit ยอดเงิน Floating P/L การดูแลไม้และเหตุผล
2. หน้า Intelligence: กด Refresh เองและรักษาตำแหน่ง Scroll แสดง Top 10 และกาง Top 100 ได้ ข้อมูลที่ไม่แสดงยังถูกเก็บและนับจำนวน

### ความปลอดภัย
Pack นี้ไม่เรียก MT5 order_send ไม่ให้ Execution Permission และไม่ข้าม Risk, Trading Cost, Profile Capacity หรือ Execution Gate เดิม

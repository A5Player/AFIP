# AFIP Milestone P Pack 3 — การวิเคราะห์ลำดับพฤติกรรมตลาด

แพตช์นี้เพิ่มการวิเคราะห์ State จาก Milestone P Pack 2 ตามลำดับเวลาแบบ deterministic, immutable และใช้เพื่อการวิจัยเท่านั้น

## ขอบเขต

- ตรวจ lineage ของ normalized state จาก Pack 2
- บังคับ State ID ไม่ซ้ำและต้องมีอย่างน้อย 3 State
- รักษาหลัก Market Regime before Behaviour
- สร้าง transition signature และจำนวนการเปลี่ยน Regime, Behaviour และ Direction
- วัด Persistence และหา Regime/Behaviour หลักแบบ deterministic
- ตรวจ Data Quality, Future Safety, XM Only, GOLD# Only และ 1 Unit = 0.01 Lot

## ความปลอดภัย

Runtime ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน Trading Logic เลื่อนข้อมูลเป็น Production Knowledge แก้ Position สร้าง Broker Request หรือส่งคำสั่งซื้อขาย

Execution ยังคง `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

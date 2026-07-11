# AFIP Milestone P Pack 2 — Market Behaviour State Normalization

แพ็กนี้ทำให้ Market Behaviour Observation ที่ผ่าน Milestone P Pack 1 อยู่ใน schema มาตรฐานเดียวกันแบบ immutable สำหรับงานวิจัยเท่านั้น

## ขอบเขต

- ตรวจ lineage และสถานะ READY จาก Pack 1
- รักษาหลัก Market Regime before Behaviour
- ทำมาตรฐาน Direction, Liquidity, Regime, Behaviour State และค่าตัวชี้วัด
- สร้างค่า Directional Strength, Volatility State, Range Zone และ Momentum State แบบ deterministic
- ระงับข้อมูลที่ไม่ผ่านการรับรอง, Future Leakage, ลำดับเวลาผิด, ป้ายกำกับผิด, ค่าที่ไม่เป็นตัวเลขหรืออยู่นอกช่วง และการละเมิดนโยบายล็อก

## ความปลอดภัย

Runtime นี้ใช้เพื่อการวิจัยเท่านั้น ไม่มีสิทธิ์ปรับพารามิเตอร์ เปลี่ยน Trading Logic เลื่อนข้อมูลเป็น Production Knowledge แก้ Position สร้าง Broker Request หรือส่งคำสั่งซื้อขาย

Execution ยังคง `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

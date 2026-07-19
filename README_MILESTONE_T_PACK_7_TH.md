# AFIP Milestone T Pack 7

## มาตรฐานเริ่มต้นจากผลงานวิจัย การเลือกตามสถานการณ์ และฐานการดึงข้อมูลย้อนหลังสูงสุด

Pack นี้ดำเนินการตามคำตัดสินของเจ้าของระบบว่า ผลงานวิจัยที่ผ่าน Walk-Forward, Robustness และ Evidence Gate ถือเป็นหลักฐานพิสูจน์แล้ว สามารถนำมาเป็นมาตรฐานเริ่มต้นได้ทันทีโดยไม่ต้องรอรอบพิสูจน์ซ้ำอีกครั้ง

## ความสามารถ

- มาตรฐานเริ่มต้นจากงานวิจัยแบบมี Version
- บันทึกการอนุมัติโดยเจ้าของระบบอย่างชัดเจน
- Evidence Lineage และ Dataset Lineage ครบถ้วน
- เลือก Policy ตามบริบทตลาดแบบ Deterministic
- เลือกผลวิจัยที่มีหลักฐานดีที่สุดภายในบริบทที่ตรงกัน
- รองรับ Supersede และประวัติสำหรับ Rollback
- อนุญาตให้ Manifest ของมาตรฐานมี `production_usable = true`
- วางแผนดึงข้อมูลย้อนหลังตั้งแต่ข้อมูลแรกสุดที่หาได้ถึงแท่งปิดล่าสุด
- รวมบริบท GOLD, DXY, EURUSD, GBPUSD, USDJPY, USOIL, UKOIL, US500 และ US30
- Timeframe M1, M5, M15, M30, H1, H4 และ D1
- Dataset แบบ Append-only พร้อมตรวจสอบย้อนกลับ

## ขอบเขตความปลอดภัย

Registry สามารถประกาศมาตรฐานที่อนุมัติแล้วว่าใช้งานได้ แต่ Registry ไม่ส่ง Order และไม่มีสิทธิ์ข้าม Risk, Trading Cost, Position Sizing, Execution Permission, Demo Gateway หรือ MT5 Order Control เดิม

## ฐานที่ใช้

- Commit ก่อนหน้า: `89d20bfa26746bab87507e179633f0dff52f7eb4`
- Pack 6 Full Regression: 2188 passed
- Pack 7 Focused Tests: 24 passed
- Pack 7 Full Regression: 2212 passed
- Runtime ระหว่างตรวจ: LOCKED_SIMULATION_ONLY

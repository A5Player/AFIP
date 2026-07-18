# AFIP Milestone T Pack 5

## การรวมผลทดลอง Exit การแบ่งบริบท และการประเมินหลักฐาน

Patch นี้เพิ่มชั้นวิเคราะห์หลักฐานแบบ Research Only เหนือ Position Outcome จาก Milestone T Pack 4

### สิ่งที่เพิ่ม

- Evidence Observation แบบ Deterministic
- การแบ่งผลตามบริบทตลาด
- การรวมผลตาม Policy และ Context
- ค่า Expectancy, Dispersion, Consistency, Exit Quality และ Capital Preservation
- การประเมินความเพียงพอของหลักฐานเพื่อการวิจัย
- การเปรียบเทียบ Policy แบบคู่โดยไม่เลือกผู้ชนะ
- Dataset แบบ Append-only พร้อมตรวจสอบ Checksum Chain
- Research Quarantine Metadata

### มิติบริบท

- Market Regime
- Market Structure
- Liquidity
- Trend
- Volatility
- Trading Session
- Direction
- Pattern Family

### ขอบเขตความปลอดภัย

- Research State: `EXPERIMENTAL`
- Production Usable: `false`
- ไม่อนุญาต Automatic Promotion
- ไม่มีคำสั่ง MT5 Order/Check/Send/Modify/Close
- Production Runtime ไม่เปลี่ยน
- Production Trading Logic ไม่เปลี่ยน

### Validation

รัน `RUN_MILESTONE_T_PACK_5.ps1` หรือ `RUN_MILESTONE_T_PACK_5.bat`

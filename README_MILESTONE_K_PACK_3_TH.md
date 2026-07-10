# Milestone K Pack 3 — Smart Exit Engine

เพิ่มการวางแผนออกจากสถานะแบบ deterministic อธิบายได้ และจำกัดเฉพาะ Simulation สำหรับ XM / GOLD#

รองรับ:
- HOLD
- PARTIAL_CLOSE
- EXIT

ระบบตรวจจำนวน Unit, นโยบาย 1 Unit = 0.01 Lot, ราคาอ้างอิง, ความเสี่ยง, เวลา, ต้นทุน และนโยบายการส่งคำสั่ง โดยไม่แก้ไขสถานะจริงและไม่ส่งคำสั่งไป MT5

รัน:
```powershell
.\RUN_MILESTONE_K_PACK_3.ps1
```

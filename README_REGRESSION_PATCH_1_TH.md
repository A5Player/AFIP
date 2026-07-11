# AFIP Regression Patch 1 — การลงทะเบียน Dashboard Panel

Patch นี้แก้ Regression ของ Dashboard จำนวน 6 Panel ซึ่งถูกพัฒนาไว้แล้วใน Milestone ก่อนหน้า แต่ยังไม่ได้ลงทะเบียนใน `DashboardUIRuntime`

## ขอบเขต
- แก้ Regression เท่านั้น
- ไม่ใช่ Feature ใหม่
- ไม่เปลี่ยน Trading Logic
- ไม่เปลี่ยน Intelligence Engine
- ไม่เปิดการส่งคำสั่งซื้อขาย

## Panel ที่คืนกลับ
- `production_readiness_complete`
- `knowledge_intelligence_foundation`
- `pattern_knowledge_engine`
- `pattern_similarity_search`
- `pattern_clustering`
- `pattern_statistics`

## สถานะความปลอดภัย
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: `False`
- Live execution: `Disabled`
- Order status: `NO_ORDER_SENT`

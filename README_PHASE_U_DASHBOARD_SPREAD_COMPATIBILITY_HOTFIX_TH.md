# AFIP Phase U Dashboard Spread Compatibility Hotfix

แก้ Backward Compatibility ของ `_profile_rows()` โดยคืนแถวเดิม:

- Bid
- Ask
- Spread

แถว `Spread` ใช้ชื่อสัญญาเดิมตรงตัวและแสดงรูปแบบ `<value> points` เพื่อให้ regression test เดิมผ่าน โดยไม่เปลี่ยน MT5, Execution หรือ Lot Authority

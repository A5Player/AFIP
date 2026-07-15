# AFIP Milestone S Pack 4.7

แพ็กกู้คืนความเข้ากันได้ย้อนหลังของระบบจัดสรรทุน

## การแก้ไข
- แก้การตรวจ Allocation Mode ไม่ให้ `LEGACY_FIXED_UNIT` ไหลไปเป็น `allocation_mode_unknown`
- รองรับครบทั้ง `LEGACY_FIXED_UNIT`, `CAPITAL_TIER_TABLE`, `RESEARCH_FIXED_001`
- คงตาราง P1/P2 ที่อนุมัติใน Pack 4.6
- คืนค่า Diagnostic เดิมที่ Test และ Operator ใช้งาน
- ไม่ลด Safety Gate ใด ๆ

## ผลทดสอบ
- Pack regression 17 passed
- Full regression 1812 passed

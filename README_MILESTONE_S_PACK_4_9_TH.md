# Milestone S Pack 4.9 — Emergency Execution Safety

แพ็กนี้แก้กติกาความปลอดภัยหลักแบบ Fail-Closed:

1. `maximum_units` เป็นเพดานสูงสุด ไม่ใช่จำนวนที่ต้องเปิด
2. จำนวนไม้จริงเท่ากับค่าต่ำสุดจากทุน, confidence, risk, margin และความจุคงเหลือ
3. ทุนไม่ถึง `capital_per_unit` ต้องเปิด 0 ไม้
4. ไม่มี Adaptive Protection Plan ต้องไม่ส่งออเดอร์
5. ปฏิเสธ fallback แบบ TP 500 จุด / SL 3000 จุดโดยตรง
6. ต้องระบุแหล่ง SL, แหล่ง TP และ planned horizon
7. Profile เป็น metadata; allocation คำนวณจาก config snapshot และสถานะบัญชีจริง

## คำเตือน

แพ็กนี้เพิ่ม Protection Control และ Source Audit แต่ไม่แก้ execution gateway แบบเดาสุ่ม
เพราะตำแหน่ง gateway ต้องตรวจจาก Source ล่าสุดของเครื่องผู้ใช้

ให้รัน:

```powershell
python -m pytest tests\test_milestone_s_pack_4_9_emergency_execution_safety.py -v
python tools\afip_pack_4_9_source_audit.py
```

ผล Audit จะอยู่ที่:

```text
runtime/audit/milestone_s_pack_4_9_source_audit.json
```

ก่อนเปิด Runner อีกครั้ง ต้องนำ `approve_execution()` ไปวางทันทีหน้า
`MT5 order_check` และ `MT5 order_send` ใน execution gateway จริง

# AFIP Phase U Pack 3.3.8 — แก้ Position Sizing Authority และ CI

แตก ZIP ทับที่ราก Repository แล้วรัน `RUN_PHASE_U_PACK_3_3_8.ps1`

จุดสำคัญ:
- P1-P3 ใช้ `CAPITAL_TIER_TABLE` เป็น Authority เดียว
- `capital_per_unit` คงไว้เพื่อรองรับไฟล์เก่า แต่ไม่มีอำนาจคำนวณ Tier
- P1/P2/P3 เปิด participation ตามแผนล่าสุด
- P4 คงเป็น Research fixed 0.01
- แก้ Constructor compatibility ที่ทำให้ CI ล้ม 20 tests
- ไม่เปิด Direct/Live execution และยังคง `LOCKED_SIMULATION_ONLY`

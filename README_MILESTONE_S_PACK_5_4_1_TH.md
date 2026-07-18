# AFIP Gold V1.0 — Milestone S Pack 5.4.1

## วัตถุประสงค์
คืนสถานะเปิดใช้งานให้โปรไฟล์เดโมทั้งสี่ผ่านไฟล์ configuration ซึ่งเป็น source of truth ของระบบ

## สาเหตุ
`config/four_profile_demo.json` ระบุ `enabled=false` สำหรับ P2 และ P3 โดยตรง Configuration Loader และ Profile Manager จึงหยุดสองโปรไฟล์นี้อย่างถูกต้องก่อนถึงการตรวจ Demo Execution Gateway

## การแก้ไข
กำหนด P1, P2, P3 และ P4 เป็น `enabled=true` ครบทั้งหมด

ไม่มีการ bypass loader, ไม่มี runtime override, ไม่ลด safety threshold และไม่ปลดล็อก execution

## สถานะความปลอดภัย
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: ปิด
- Live execution: ปิด
- Trading cost, spread, risk, capital, profile policy และ execution permission: ไม่เปลี่ยนแปลง

## การตรวจสอบ
เปิด virtual environment แล้วรัน `RUN_MILESTONE_S_PACK_5_4_1.ps1` จาก repository root

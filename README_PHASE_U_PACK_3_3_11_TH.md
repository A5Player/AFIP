# AFIP Phase U Pack 3.3.11

## Runtime Research Data Git Isolation

Pack นี้แยกข้อมูลวิจัยที่ AFIP สร้างระหว่างรันออกจาก Source Repository โดย **ไม่ลบข้อมูลในเครื่องหรือ VPS**

## ขอบเขต

- Ignore ไฟล์ JSONL ที่ Automatic Research สร้างขึ้น
- Ignore Historical Data Lake และพื้นที่ทำงานสำหรับ Resume/Export/Quarantine
- นำไฟล์ Schema V2 ที่ Git ติดตามอยู่ 5 ไฟล์ออกจาก Git index เท่านั้น
- ไฟล์จริงยังอยู่ในเครื่องครบ
- Source Code, Config, Tests, Documentation และ Fixture ที่จำเป็นยังอยู่ภายใต้ Git
- ไม่เปลี่ยน Trading Logic
- ไม่เปลี่ยน Lot Size, SL, TP หรือ Position Sizing
- ไม่ปลดล็อก Real Execution และไม่เปลี่ยน P1 เป็นบัญชีเงินจริง

## ไฟล์ที่นำออกจาก Git index

```text
runtime/research/automatic/schema_v2/candidates.jsonl
runtime/research/automatic/schema_v2/decisions.jsonl
runtime/research/automatic/schema_v2/run_summaries.jsonl
runtime/research/automatic/schema_v2/snapshots.jsonl
runtime/research/automatic/schema_v2/timeline.jsonl
```

## วิธีติดตั้ง

แตก ZIP แล้วนำไฟล์ทั้งหมดไปทับ Repository เดิม จากนั้นรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_PHASE_U_PACK_3_3_11.ps1
.\RUN_PHASE_U_PACK_3_3_11.ps1
git status
```

หลังรัน Apply ใน `git status` อาจเห็นไฟล์ 5 รายการเป็น deleted ซึ่งหมายถึง **ลบออกจาก Git index** ไม่ใช่ลบจาก VPS หลัง Commit แล้วไฟล์เหล่านี้จะยังคงถูก AFIP เขียนต่อได้ตามปกติ แต่จะไม่ติด Git อีก

## ข้อควรระวังสำหรับ P1เงินจริง

Pack นี้เป็น Data/Git Isolation เท่านั้น ไม่ใช่ Production Live Certification ห้ามถือว่าการผ่าน Pack นี้เป็นหลักฐานว่า P1 พร้อมใช้เงินจริง ต้องตรวจ Lot Size, Capital Gate, Max Units, SL/TP, Drawdown Protection, Broker Mapping, Real Account Confirmation และ Emergency Stop แยกต่างหากก่อนเปิดเงินจริง

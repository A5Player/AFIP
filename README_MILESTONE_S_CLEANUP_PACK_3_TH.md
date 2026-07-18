# Milestone S Cleanup Pack 3 — Exact Source Evidence

Pack 2 ยืนยัน Candidate Owners แล้ว แต่ยังไม่ควรเปลี่ยน Runtime โดยไม่อ่าน
Source จริง เพราะรายงาน dependency พบว่า:

- Demo Gateway เป็นเจ้าของ `order_send` และ `order_check`
- Unit Allocation owner candidate มีอยู่จริง
- แต่ Demo Gateway ยังไม่พบ direct dependency ไปหา Unit Allocation owner
- Demo Gateway ใช้ `four_profile_operations` และ `capital_growth_engine`
  ในเส้นทางปัจจุบัน

Pack 3 จึงรวบรวมเฉพาะ Source ที่เกี่ยวข้องจริง พร้อม function bodies,
imports, calls และบรรทัดที่เกี่ยวกับ:

- allocated_units / maximum_units
- capital_per_unit / base_lot
- order_check / order_send
- TP / SL
- ATR / Buffer
- Risk Approval
- Profile capacity

## วิธีรัน

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\AFIP
.\RUN_MILESTONE_S_CLEANUP_PACK_3.ps1
```

หลังรัน ส่งไฟล์นี้กลับมา:

```text
runtime\architecture_cleanup_pack_3\AFIP_CLEANUP_PACK_3_SOURCE_EVIDENCE_RESULT.zip
```

ไฟล์นี้ไม่มี `.venv`, runtime logs ขนาดใหญ่ หรือข้อมูล MT5 credentials

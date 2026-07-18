# Milestone S Cleanup Pack 1 — Complete Architecture Inventory

แพ็กนี้เป็นจุดเริ่มต้นของ AFIP Production Cleanup & Certification

## เป้าหมาย

- หยุดเพิ่ม Feature ใหม่
- ตรวจทุก Python module ใต้ `afip/`
- สร้างทะเบียน Intelligence, Engine, Runtime, Planner, Gateway และ Research
- หาโมดูลที่มีหน้าที่ซ้ำ
- หาทุกจุดที่มีอำนาจเกี่ยวกับ:
  - `order_send`
  - `order_check`
  - Unit Allocation
  - Position Sizing
  - SL/TP Protection
  - Risk Approval
- ตรวจ legacy execution defaults แบบ strict pattern:
  - TP 500
  - SL 3000
  - บังคับ 3 units
  - ใช้ maximum_units เป็น allocated_units
- สร้าง Certification Blockers โดยอัตโนมัติ

## แพ็กนี้ไม่ทำอะไร

- ไม่ลบโมดูล
- ไม่ Refactor
- ไม่แก้ Trading Logic
- ไม่เปิดออเดอร์
- ไม่เพิ่ม Intelligence หรือ Engine

มันสร้างหลักฐานจาก Source จริง เพื่อใช้ตัดสินใจใน Cleanup Pack 2

## วิธีรัน

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\AFIP
.\RUN_MILESTONE_S_CLEANUP_PACK_1.ps1
```

## ไฟล์ผลลัพธ์

```text
runtime\architecture_inventory\ARCHITECTURE_INVENTORY.md
runtime\architecture_inventory\architecture_review.json
runtime\architecture_inventory\components.json
runtime\architecture_inventory\components.csv
```

หลังรันแล้ว ให้ส่งไฟล์ `architecture_review.json` และ
`ARCHITECTURE_INVENTORY.md` กลับมา เพื่อสร้าง Cleanup Pack 2 แบบอิง Source จริง

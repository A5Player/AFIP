# Revision 1

แก้ PowerShell native-command handling ตอนตรวจไฟล์ untracked โดยไม่เปลี่ยนขอบเขตการทำงานของแพ็ก

# AFIP V1 Final Production Certification Pack

แพ็กนี้ทำความสะอาด Repository และตรวจความพร้อมก่อน Commit/Push โดยไม่แก้ Trading Logic

## สิ่งที่แพ็กทำ

- กู้คืนไฟล์ ZIP ที่ถูกลบโดยไม่ตั้งใจ หากไฟล์นั้นยังเป็น tracked file
- คืนค่า generated runtime/dashboard snapshots ที่ถูกเปลี่ยนจากการรัน Dashboard
- ลบเฉพาะ untracked runtime snapshots และ extracted patch workspace ที่ระบุชัดเจน
- เพิ่ม exact ignore rules สำหรับ runtime-only files
- รัน repository audit
- รัน `git diff --check`
- รัน focused production certification
- ไม่รัน MT5
- ไม่เปิด Runtime
- ไม่ stage, commit หรือ push อัตโนมัติ
- ไม่เปลี่ยน Signal, Lot Authority, SL/TP, Risk Gate หรือ Execution Authority

## วิธีติดตั้ง

แตก ZIP ที่อื่น แล้วคัดลอกทุกไฟล์และโฟลเดอร์ไปทับ:

```text
C:\AFIP
```

## วิธีรัน

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_FINAL_PRODUCTION_CERTIFICATION.ps1
```

เมื่อขึ้น `PASS` ให้รัน:

```powershell
git status
git diff --stat
python -m pytest
git add .
git commit -m "AFIP V1 Final Production Certification"
git push origin main
```

ก่อน `git add .` โปรดตรวจ `git status` ว่าไม่มี credentials, account secrets, `.venv`, runtime snapshots หรือไฟล์ส่วนตัวติดมาด้วย

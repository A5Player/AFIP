# AFIP Milestone S Pack 5.8 — Blind Forward Research Engine

## วัตถุประสงค์

เพิ่ม Engine วิจัยแบบเดินหน้าเท่านั้น เพื่อประเมิน Candidate TP, SL และ Time Exit หลายรูปแบบ โดยใช้เฉพาะแท่งที่ปิดหลังเวลา Entry ของกรณีวิจัยอย่างเคร่งครัด

## พฤติกรรมที่รับรอง

- ปฏิเสธแท่งที่เวลาเท่ากับหรือก่อน Entry
- ตรวจลำดับเวลาเพื่อป้องกัน Look Ahead
- Candidate TP/SL/Time Exit มาจากไฟล์ Configuration ไม่ Hardcode ใน Trading Policy
- เก็บ MAE, MFE, จำนวนแท่งถือ และเวลาถือ
- หาก TP และ SL ถูกแตะในแท่งเดียวกัน ให้ SL First
- มี SHA-256 Input Hash และ Result ID แบบ Deterministic
- ผลวิจัยเป็น Append-only JSONL พร้อมกันข้อมูลซ้ำและ Manifest
- มี Research Eligibility และ Quarantine Reasons
- ฐานข้อมูลวิจัยใช้ร่วมกันระหว่าง P1–P4
- Execution Authority ของ Engine นี้เท่ากับ `NONE`

## การติดตั้ง

คัดลอกไฟล์ใน Patch ทับลง Repository AFIP โดยรักษาโครงสร้างโฟลเดอร์เดิม

## การตรวจสอบ

```powershell
.\RUN_MILESTONE_S_PACK_5_8.ps1
python tools/afip_local_quality_check.py
pytest
```

Pack นี้ไม่เปิด MT5 Execution, Demo Execution หรือ Live Execution

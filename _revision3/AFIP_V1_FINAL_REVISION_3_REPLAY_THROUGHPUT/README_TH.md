# AFIP V1 Final Revision 3 — Replay Throughput Optimization

แพ็กนี้เป็น Patch Only สำหรับลดคอขวดของ Automatic Historical Replay โดยไม่เปลี่ยน Trading Logic, Candidate Logic, Dataset Contract, Resume Contract หรือ Append-only Integrity

## การแก้ไขรวมในแพ็กเดียว

1. เปลี่ยน progress callback จากทุก 1 bar เป็น adaptive interval
   - ค่าอัตโนมัติประมาณ 1% ของจำนวนแท่ง
   - ต่ำสุด 5 bars
   - สูงสุด 50 bars
   - รองรับการกำหนด `progress_interval_bars` เอง
2. จัดกลุ่ม bars ตาม timeframe เพียงครั้งเดียว ลดการสแกนข้อมูลซ้ำ
3. ลดการเขียน Automatic Research Status และ Runtime Observatory ตามจำนวน callback ที่ลดลง
4. เพิ่ม `runtime/research/replay_performance.json` เพื่อบันทึก throughput และจำนวน status updates
5. เพิ่ม validation สำหรับ `maximum_replay_bars` และ `progress_interval_bars`
6. ไม่มี MT5 order send/check และไม่เพิ่มสิทธิ์ execution

## ไฟล์ลงทับ

- `afip/automatic_research_runtime/runtime.py`

## ไฟล์เพิ่ม

- `tests/test_revision_3_replay_throughput.py`

## วิธีติดตั้ง

จาก `C:\AFIP\source`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Expand-Archive .\AFIP_V1_FINAL_REVISION_3_REPLAY_THROUGHPUT.zip -DestinationPath .\_revision3 -Force
.\_revision3\INSTALL_REVISION_3.ps1 -ProjectRoot C:\AFIP\source
```

## วิธีทดสอบ

```powershell
cd C:\AFIP\source
.\.venv\Scripts\Activate.ps1
python -m pytest tests\test_revision_3_replay_throughput.py tests\test_phase_u_pack_3_2_automatic_research_runtime.py tests\test_milestone_t_pack_3_historical_replay_runner.py -v
python tools\afip_local_quality_check.py
```

## วิธีรัน Automatic Research อีกครั้ง

ใช้คำสั่งเดิมของ AFIP ที่เรียก Automatic Research Runtime แล้วตรวจ:

```powershell
Get-Content .\runtime\research\automatic_research_status.json
Get-Content .\runtime\research\replay_performance.json
Get-Content .\runtime\research\runtime_observatory_status.json
```

ไฟล์เดิมจะถูกสำรองไว้ใน `_revision3_backup` ก่อนลงทับ

# Milestone S Pack 1 — ระบบรัน Locked Simulation ต่อเนื่อง

เพิ่มตัวรันสำหรับทดสอบ Locked Simulation Acceptance อย่างต่อเนื่องบน Windows VPS

## คำสั่ง

```powershell
python afip.py run-locked-simulation
```

ทดสอบแบบกำหนดจำนวนรอบ:

```powershell
python afip.py run-locked-simulation 60 3
```

ค่าตัวแรกคือจำนวนวินาทีต่อรอบ และค่าตัวที่สองคือจำนวนรอบสูงสุด

## ความปลอดภัย

- คง `LOCKED_SIMULATION_ONLY`
- ปิด Direct Execution
- ปิด Live Execution
- ทุก Cycle ยืนยัน `NO_ORDER_SENT`
- ไม่เรียก Broker Order API
- หยุดอย่างปลอดภัยด้วย `Ctrl+C`

## ไฟล์ Runtime

- `runtime/locked_simulation/status.json`
- `runtime/locked_simulation/events.jsonl`
- `runtime/locked_simulation/acceptance_summary.json`

Snapshot ที่เหมือนรอบก่อนหน้าจะถูกตรวจด้วย fingerprint และไม่บันทึกซ้ำ

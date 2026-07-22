# AFIP Phase V Major Pack

ชุดสุดท้ายสำหรับโหลดข้อมูลย้อนหลัง ทำ replay/วิจัยต่อเนื่อง และติดตามสถานะจนถึงปัจจุบัน โดยใช้ระบบวิจัยเดิมของ AFIP เป็นฐาน ไม่สร้างสูตรข้อมูลหรือ execution authority ซ้ำ

## ลำดับสถานะ
DATA_LOADING → CONTINUOUS_RESEARCH → LIVE_READY

## ความปลอดภัย
- ค่าเริ่มต้น `DATA_ONLY`
- ไม่มีคำสั่ง order send ในโมดูลนี้
- ไม่เปิด Live Execution จากการติดตั้งหรือการรัน validation
- นโยบายวิจัยเลื่อนเป็น active certified research policy ได้เฉพาะเมื่อมีหลักฐานครบ: walk-forward, out-of-sample, drawdown, stability, no leakage และ sample size
- การเลื่อนนโยบายไม่แก้ execution config โดยตรง
- Live ต้องตั้ง `mode` เป็น `LIVE_EXECUTION`, ผ่าน readiness และมีไฟล์ arm จากคำยืนยัน exact phrase

## ใช้งาน
1. รัน validation: `./RUN_PHASE_V_MAJOR_PACK.ps1`
2. ตรวจ `runtime/research/phase_v_major_status.json`
3. เริ่มรันยาว: `./START_AFIP_LONG_RUN.ps1`
4. ดูสถานะ: `./STATUS_AFIP_LONG_RUN.ps1`
5. หยุด: `./STOP_AFIP_LONG_RUN.ps1`

## การ Arm Live
ใช้เฉพาะหลัง full regression, GitHub Actions, data/research readiness และ dashboard แสดง LIVE_READY:
`./ARM_AFIP_LIVE_EXECUTION.ps1 -Confirmation "ARM AFIP LIVE EXECUTION"`

การ arm ใน Pack นี้เป็น readiness flag เท่านั้น ไม่เพิ่ม order-send path ใหม่ และไม่ bypass execution safety เดิม

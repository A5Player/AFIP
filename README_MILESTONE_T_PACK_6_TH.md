# AFIP Milestone T Pack 6

## Robustness, Walk-Forward Validation & Research Promotion Evidence Gate

Pack 6 เพิ่มชั้นตรวจสอบความน่าเชื่อถือของหลักฐานวิจัยจาก Pack 4 และ Pack 5 โดยทำงานแบบ Deterministic และเป็น Research-only เท่านั้น

## ขอบเขต

- แบ่งข้อมูลตามลำดับเวลาเป็น Train / Validation / Forward
- บังคับ No Future Leakage
- คำนวณ Temporal Stability
- วัดการเสื่อมลงระหว่าง Train, Validation และ Forward
- จำลองผลกระทบจาก Spread, Slippage, Volatility, Liquidity, Session และ Gap
- คำนวณ Resilience และ Robustness
- สร้าง Promotion Evidence Score
- บังคับ Human Approval
- เชื่อม Research Quarantine
- Dataset เป็น Append-only พร้อม Checksum Chain
- Metadata พร้อมใช้แสดงผลใน Dashboard

## สัญญาด้านความปลอดภัย

- Patch Only
- Backward Compatible
- Production Trading Logic ไม่เปลี่ยน
- Production Runtime ไม่เปลี่ยน
- ไม่มีคำสั่ง MT5 Order
- `LOCKED_SIMULATION_ONLY`
- ทุก Record เป็น `EXPERIMENTAL`
- ทุก Record เป็น `production_usable = false`
- ห้าม Promote อัตโนมัติ
- แม้ผ่าน Gate จะได้เพียง `PROMOTION_CANDIDATE_RESEARCH_ONLY`

## Dataset ใหม่

- `walk_forward_windows`
- `walk_forward_observations`
- `walk_forward_results`
- `robustness_scenarios`
- `robustness_results`
- `promotion_evidence_records`

## ผลตรวจในเครื่องสร้าง Patch

- Focused Tests: `20 passed`
- Financial Naming: `PASS`
- Local Quality: `PASS`
- Full Regression: `2188 passed`

เครื่องสร้าง Patch ไม่มีแพ็กเกจ MetaTrader5 จึงตรวจ MT5 ผ่าน Simulation Fallback ตามระบบเดิม เครื่อง Windows ของผู้ใช้จะตรวจ MT5 จริงอีกครั้งผ่าน RUN script

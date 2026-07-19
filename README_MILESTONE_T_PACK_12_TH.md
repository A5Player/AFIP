# AFIP Milestone T Pack 12

## Certified Trade Plan Runtime Orchestration

Pack นี้เชื่อมโยง Adaptive Ranking, Complete Trade Plan, Trade Plan Certification, Runtime Capital Capacity, Recovery Reconciliation, Decision Trace และ Operations Dashboard Read Model เข้าด้วยกันโดยยังคงโหมด LOCKED_SIMULATION_ONLY

หลักสำคัญ:

- ไม่มีการเพิ่ม MT5 Order Sender
- ไม่มีการเพิ่ม Execution Permission
- แผนที่ไม่ผ่านการรับรองจะไม่เข้าสู่การตรวจ Execution Gate
- จำนวนไม้ต้องผ่าน Capital, Risk, Margin, Exposure, Correlation และ Profile Capacity
- ต้องตรวจสอบสถานะการเชื่อมต่อ ข้อมูลตลาด สถานะบัญชี ตำแหน่งเปิด คำสั่งที่ไม่รู้จัก การควบคุมคำสั่งซื้อขายด้วยตนเอง สถานะ Equity และ Safe Mode ก่อนรับความเสี่ยงใหม่

ผลลัพธ์สูงสุดของ Pack นี้คือ READY_FOR_EXECUTION_GATE_REVIEW เท่านั้น

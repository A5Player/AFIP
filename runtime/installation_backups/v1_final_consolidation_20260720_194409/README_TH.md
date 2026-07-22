# AFIP Version 1.0 Final Consolidation

Pack ใหญ่ชุดสุดท้ายนี้สร้างจาก AFIP(44).zip ที่แนบล่าสุดและ commit `8bd57f9` โดยตรง เป็น Patch Only และกำหนด Authority จริงเพียง 2 ชุด คือ Trading Runtime กับ Research Runtime

ทางเข้าหลักหลังติดตั้งมีเพียง `START_AFIP.ps1`, `STOP_AFIP.ps1`, `STATUS_AFIP.ps1` Dashboard หลักคือ `runtime/dashboard/afip_dashboard.html` และสถานะกลางคือ `runtime/final_integration_status.json`

สคริปต์เก่าคงไว้เฉพาะ Backward Compatibility และถูกบันทึกเป็น compatibility entry points ไม่ใช่ Production Authority

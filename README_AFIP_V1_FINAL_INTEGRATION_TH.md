# AFIP Version 1.0 Final Integration

Pack นี้เป็น Patch Only สำหรับ Repository ล่าสุด โดยเพิ่ม Authority กลางเพียงชุดเดียว และไม่เขียน Trading Logic, Risk Logic, Research Logic หรือ Historical Dataset ใหม่ซ้ำ

## Architecture สุดท้าย

- **Trading Runtime** ใช้ระบบ execution ปัจจุบัน
- **Research Runtime** รวม Phase V, Automatic Research, Historical Replay, Replay Throughput และ Runtime Observatory
- **Unified Dashboard** เหลือไฟล์หลัก `runtime/dashboard/afip_dashboard.html`
- **Background Control** ใช้ `START_AFIP.ps1`, `STOP_AFIP.ps1`, `STATUS_AFIP.ps1`
- **Historical Data Lake** ใช้ `runtime/research/historical_data_lake`
- **Incremental Index** ใช้ `runtime/research/research_file_index.json`

สคริปต์เดิมยังคงอยู่เพื่อ Backward Compatibility แต่หลังติดตั้งควรใช้สคริปต์ Final Integration สามตัวเป็นทางเข้าหลัก

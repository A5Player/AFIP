# AFIP V1 Final — Pack 4 Production Certification Repair

Install:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
cd <extracted-pack-folder>
.\INSTALL_AFIP_V1_FINAL_PACK_4.ps1 -ProjectRoot C:\AFIP\source
.\RUN_AFIP_V1_FINAL_PACK_4.ps1 -ProjectRoot C:\AFIP\source
```

Full regression after focused certification:

```powershell
cd C:\AFIP\source
python -m pytest -q
```

Rollback:

```powershell
.\ROLLBACK_AFIP_V1_FINAL_PACK_4.ps1 -ProjectRoot C:\AFIP\source
```

# AFIP Phase U Pack 3.4.9 Runtime Entrypoint Hotfix

This patch corrects two production issues discovered during the first Windows PowerShell run:

1. Direct execution of `tools/afip_phase_u_pack_3_4_9_runtime.py` placed only the `tools` directory on `sys.path`, causing `ModuleNotFoundError: No module named 'afip'`.
2. Windows PowerShell 5.1 did not stop after a non-zero native Python exit code, allowing a misleading completion message.

The runtime now resolves and inserts the repository root before package imports. The PowerShell run and validation scripts now inspect `$LASTEXITCODE` after every Python process and stop immediately on failure. The batch launcher also propagates failure.

No trading policy, thresholds, runtime authority, financial values, or research results are changed by this hotfix.

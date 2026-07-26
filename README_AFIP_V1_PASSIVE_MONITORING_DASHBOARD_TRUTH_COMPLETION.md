# AFIP V1 Passive Monitoring Dashboard Truth Completion

Patch-only dashboard/runtime observability repair. No signal, lot, SL, TP, risk, execution authority, or order-send logic is changed.

## Repairs

- Passive monitoring never calls MT5 initialize, login, reconnect, or order functions.
- Operations summary counts actual configured `terminal64.exe` processes.
- Replaces ambiguous `Fresh data` with separate truth indicators:
  - `MT5 process`
  - `Live financial`
  - `Verified snapshot`
  - `Observation current`
- Financial values are labelled as `LIVE`, `RECENT_SNAPSHOT`, `STALE_SNAPSHOT`, or `DATA_UNAVAILABLE`.
- A disconnected profile may retain its last verified snapshot, but it is never presented as live.
- Live MT5 page separates connection observation from financial evidence.
- Active diagnostic remains opt-in through `--active`.

## Expected closed-terminal example

With P1/P2 open and P3/P4 closed:

- Runtime: 4/4 (when AFIP runners remain active)
- MT5 process: 2/4
- P1/P2: CONNECTED_PASSIVE
- P3/P4: DISCONNECTED
- Live financial: 0/4 during passive observation
- Verified snapshot: up to 4/4 depending on saved verified evidence

## Install

Run the included PowerShell installer from the extracted pack directory.

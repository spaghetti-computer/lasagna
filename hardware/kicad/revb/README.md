# LASAGNA2354 (ラザニア2354) Rev.B KiCad project (PROPOSAL, NOT FAB-READY)

Status: schematic ERC 0 violations. PCB 100x100 mm, 2 layers, parts placed, **NOT ROUTED**
(499 unconnected items). Freerouting 2.1.0 left about 271 nets unrouted after 4 passes.
Do not order from fab/ yet. The gerber zip has "UNROUTED" in its name on purpose.

Regenerate with: python3 gen_sch.py; python3 gen_pcb.py; python3 export_fab.py
(design.py is the single source of truth)

## Unverified / open items
- Famicom 60-pin slot footprint: a 2x30 placeholder. Pitch and mechanics are not verified.
- DA-15 expansion pinout is not verified.
- RCA jack footprint is custom and not verified.
- $4016 parallel decode is not implemented. Only the SJ3 alternate input exists.
- CIRAM SRAM is omitted.
- Status buffer vs PPU latch contention is avoided by firmware only.
- 74HCT139 decode: possible glitch/race. Not analysed on hardware.
- LVC245 drives the cart with 3.3 V levels (assumed OK for NMOS/CMOS mask ROMs). Not verified.
- SN74AHCT574PWR (C129433) is a JLC Extended part. Stock was 0 when checked.
- Routing: needs a denser placement, or a 4-layer board, or manual routing.

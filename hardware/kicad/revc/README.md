# LASAGNA2354 (ラザニア2354) Rev.C KiCad project (PROPOSAL, NOT FAB-READY unless the status below says so)

The board uses a bare RP2354B and 7 AHCT logic ICs. Everything the board drives toward the cart is at 5 V.
Design notes are in ../revc-plan.md, section 2b.

Regenerate:
```
python3 gen_sch.py
python3 gen_pcb.py
# Specctra DSN -> Freerouting -> SES import (see the status below)
python3 export_fab.py
```

## Unverified / open
- Famicom slot footprint: a 2x30 2.54 mm placeholder. The real slot mechanics are not verified.
- RCA footprint is custom and not verified. Pad headers J4/J5 use a generic 1x7 pinout and are 3.3 V only (driven by U10 MCP23017). The Grove J9 footprint is a JST PH stand-in (unverified).
- L1: uses a Murata DFE201610P land as a stand-in for the Abracon AOTA-B201610S3R3-101-T.
  The land and the polarity dot orientation (the HDG says polarity matters) still need checking.
  LCSC showed stock 0 at check.
- QFN-80 footprint: the KiCad EP is 3.4x3.4 mm. Check it against the RP2350 datasheet package drawing.
  Pins 60 and 76 = IOVDD come from the pinout figure, because the power table omitted them.
- USB-C placement relative to the board edge must be checked in the 3D view.
- Power-down sequencing (+3V3 vs +5V_CART decay) has not been analysed.
- Freerouting does not enforce F.Cu vertical / B.Cu horizontal. That is intent only.
- Cart audio pins 45/46 are NC.

## Aesthetic pass / routing guidelines for Leo (Quilter or hand routing)
- Fab: BLACK mask, WHITE silk, HASL lead-free. See FAB_NOTES.md.
- Locked layout: row A = A1..A7 (U2 U4 U6 | U8 | U7 U5 U3), 13 mm pitch, all at the same rotation.
  CPU and PPU sides mirror exactly about x=50 (error 0.00 mm). U8 is on the centreline.
  The 100 nF decaps follow each IC's pin 20, so they are not mirrored.
- 33R AD series arrays: R10..R17 (CPU) and R20..R27 (PPU), 2.0 mm pitch at y=31, centred under columns 2 and 6, mirrored.
- Front silk: grid font 1.2 mm only (A1..A7, column numbers, row letter A, CPU/PPU) plus one title "LASAGNA2354 Rev.C".
  Refdes are on F.Fab. The back silk carries only LASAGNA2354 REV.C / MADE IN KOBE / JLCJLCJLCJLC and the TP labels; the refdes table is in FAB_NOTES.md.
- Pour: GND on B.Cu only. Do not pour on F.Cu.
- Routing style (intent; not enforced by DRC):
  - Run the buses as bundles at a constant pitch, with 45-degree bends only (no 90-degree corners).
  - F.Cu mostly vertical, B.Cu mostly horizontal.
  - Put vias in neat rows, one row per bus, at the layer change. Keep them out of the slot keepout and the crystal area.
  - Keep B.Cu breaks in the GND pour short so the bottom plane stays continuous.

## J8 removed -> test points
The J8 2x20 measurement header is gone. It is replaced by 24 THT test pads (2.0/1.0 mm, B side) in one row. See FAB_NOTES.md for the TP table.

## Pads via I2C (MCP23017) + Grove
Both pads (J4/J5) are read through U10 MCP23017 on I2C0 (GPIO44/45). U10 and the pads run at 3.3 V.
Grove J9 shares the bus. GPIO46/47 are spare, on TP G46/G47. See ../revc-plan.md section 2f.

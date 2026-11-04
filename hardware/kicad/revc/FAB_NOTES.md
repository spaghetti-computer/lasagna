# LASAGNA2354 Rev.C fab notes (PROPOSAL)

| Item | Choice |
|---|---|
| Layers / thickness | 2 layers, 1.6 mm FR4, 1 oz |
| Solder mask | **BLACK** (both sides) |
| Silkscreen | **WHITE** |
| Surface finish | **HASL lead-free** (no ENIG) |
| Min track/space, via | 0.15/0.15 mm, 0.6/0.3 mm |

The same values are in the KiCad board stackup (mask color Black, silk color White, copper_finish "HAL lead-free").
On a black board the traces are hard to see. Debugging relies on the silk grid (A1..A7) and on the refdes table in these notes, so keep the silk text where it is.

## Production-finish details (Rev.C pass 3)
- Outline 100 x 62 mm with R3 corners. 4x M3 plated mounting holes (GND) at a 4.5 mm inset.
  Each has a 4.0 mm keep-out ring with no tracks or vias.
- 3 global fiducials: Fiducial_1mm_Mask2mm (1 mm copper, 2 mm mask opening) at (6,22), (96.5,12.5) and (95,45), asymmetric.
- JLC order-number placeholder "JLCJLCJLCJLC" on the back silk (choose "specify position" when ordering).
- Teardrops are enabled on all pads. They are generated when the board is routed (Edit > Teardrops).
- Net classes:
  - Default (signal) 0.2/0.2 mm.
  - Power 0.5 mm (DRU min 0.4, max 0.6).
  - USB_90R diff pair 0.2/0.15 mm. 90 ohm is NOT achievable as microstrip over 1.6 mm FR4; the pair is short (<15 mm) at FS 12 Mbps, so this is acceptable.
- DRC rules: LASAGNA2354_RevC.kicad_dru (JLC standard: 0.127 track/space, 0.3 drill, 0.13 annular, 0.3 copper-to-edge).
- F.Fab carries the acrylic top-plate cut line (0.5 mm inside the edge), the USB-C/RCA plate cutouts and the M3 standoff zones (R3.5).
- Test points: THT pads, 2.0 mm pad / 1.0 mm drill (TestPoint_THTPad_D2.0mm_Drill1.0mm), mounted on the B side, no BOM part.
  They take a 1.0 mm pin or a probe. One row of 24 at a 3.5 mm pitch on y=57, for a bed-of-nails jig.
  Signal-name labels are on the back silk only; there is no TP text on the front.
- Silk: front = logo + LASAGNA2354 + REV.C. Back = "LASAGNA2354 REV.C" / "MADE IN KOBE", JLCJLCJLCJLC and the TP labels only.
  The spec line and the IC cross-reference table live here in the fab notes only (U2=A1, U4=A2, U6=A3, U8=A4, U7=A5, U5=A6, U3=A7). There is no date-code, S/N, QC or rating block.

| TP | net | label |
|---|---|---|
| TP1 | GND | GND |
| TP2 | +5V_CART | 5V |
| TP3 | CA0 | A0 |
| TP4 | XCD0 | D0 |
| TP5 | M2_CART | M2 |
| TP6 | CART_RW | RW |
| TP7 | CART_ROMSEL_N | RS |
| TP8 | CPU_ALE | ALE |
| TP9 | IRQ_N | IRQ |
| TP10 | OUT_OE_N | OE |
| TP11 | +3V3 | 3V3 |
| TP12 | SPARE_GP46 | G46 |
| TP13 | SPARE_GP47 | G47 |
| TP14 | +1V1 | 1V1 |
| TP15 | CVBS | VID |
| TP16 | CIRAM_A10 | A10 |
| TP17 | CIRAM_CE_N | CE |
| TP18 | PPU_DEN_N | DEN |
| TP19 | PPU_ALE | ALE |
| TP20 | CART_RD_N | RD |
| TP21 | CART_WR_N | WR |
| TP22 | XPD0 | D0 |
| TP23 | PA0 | A0 |
| TP24 | GND | GND |
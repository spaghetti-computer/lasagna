# LASAGNA2354 Rev.C — dump-only build: hand-soldered parts (1 board)

- PCBA uses only JLC **Basic** parts: `fab/LASAGNA2354_RevC_BOM_DUMP_BASIC.csv` / `CPL_DUMP_BASIC.csv`, 16 lines, 78 parts.
- Everything below is **Extended or THT** and is hand-soldered by Leo (hot plate).
- Prices and stock were read from the JLC parts API on 2026-10-13 (USD, smallest price tier). The minimum order is LCSC's.
- Buy the parts from JLC Parts / LCSC and have them shipped together with the PCB order.

| Ref | Part | LCSC | Unit $ | Need | MOQ | Buy $ | Note |
|---|---|---|---|---|---|---|---|
| U1 | RP2354B QFN-80 | C39843328 | 1.520 | 1 | 1 | 1.52 | Hot plate. Check pin 1 and the EP |
| U2,U3 | SN74AHCT573PWR | C141311 | 0.532 | 2 | 1 | 1.06 | |
| U4,U5 | 74AHCT245PW | C173388 | 0.334 | 2 | 5 | 1.67 | |
| U6,U7 | 74AHCT541PW | C84548 | 0.215 | 2 | 5 | 1.08 | |
| U8 | SN74AHCT540PWR | C7626 | 0.630 | 1 | 1 | 0.63 | Stock 610 |
| U9 | NCP1117ST33T3G | C26537 | 0.233 | 1 | 5 | 1.16 | AMS1117 (Basic, C6186) is possible, but NCP1117 is kept for its stability with ceramic output caps (HDG) |
| U11 | XC61CN3002MR-G | C2456348 | 0.187 | 1 | 5 | 0.94 | Power-down protection |
| L1 | AOTA-B201610S3R3-101-T | C42411119 | 0.315 | 1 | 5 | 1.57 | **JLC now has 285 in stock.** Dot = +1V1 |
| Y1 | ABM8-272-T3 12 MHz | C20625731 | 0.622 | 1 | 1 | 0.62 | The Basic C9002 is 20 pF load and does not match the Minimal's 15 pF caps, so Y1 is not swapped |
| J1 | USB-C TYPE-C-31-M-12 | C165948 | 0.186 | 1 | 5 | 0.93 | |
| F1 | PTC 500 mA 1206 | C46641012 | 0.041 | 1 | 10 | 0.41 | |
| R7,R8 | 27 Ω 0402 | C25100 | 0.002 | 2 | 100 | 0.19 | No Basic 27 Ω exists. Kept at the Minimal value; 22 Ω (Basic C25092) was not adopted |
| J7 | SWD 1×3 pin header | Akizuki 100167 | ¥35 | 1 | 1 | ¥35 | Optional; not needed if dumping over USB only |
| J3 | Hirose CR22A-60D-2.54DS(70) | owned | — | 1 | — | ¥0 | |

**Total from LCSC/JLC: $11.79 (about ¥1,770)**, plus the Akizuki header at ¥35 (optional).

DNP in this build: J6/R90–R92 (CVBS), J9/U10/R51–R53/C27 (Grove/MCP23017), J4/J5/R42/R43 (pad headers).
Design change: D1 moved from C72043 (green, EOL, stock 1) to **C2286 KT-0603R red (Basic)**.

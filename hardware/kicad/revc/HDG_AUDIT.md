# LASAGNA2354 Rev.C: RP2354B circuit audit against the RP2350 guidance (2026-10-13)

## Sources

| Short name | Document |
|---|---|
| HDG | "Hardware design with RP2350", datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf |
| DS | "RP2350 Datasheet", datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |

Page numbers are the printed page numbers. The Pico 2 schematic (Pico 2 datasheet, App. B) was not downloaded; DS Fig. 25 (its regulator section) was used instead.

## Audit table

| # | Item | Guide requirement (source) | Ours | Result |
|---|---|---|---|---|
| 1 | VREG_VIN | 3.3 V; CIN >= 4.7 uF, ESR <= 50 mOhm, own GND via to EP (HDG 2.1 p5-7; DS 6.3.8.1-2 p411-412) | pin 64 = +3V3, C5 4.7 uF 0603 X5R at the pin | OK (layout ?) |
| 2 | VREG_LX / L1 | shielded, 3.3 uH +-20%, DCR <= 250 mOhm, Isat >= 1.5 A, polarity-marked, oriented as Fig. 26 (DS 6.3.8.2 p412) | AOTA-B201610S3R3-101-T (DCR 140 mOhm max, Isat 2.4 A) | OK part / ? stock + land |
| 3 | COUT | 4.7 uF +-20%, ESR <= 250 mOhm, ESL <= 6 nH, as close to the pins as possible (DS 6.3.8.1-2) | C6 4.7 uF 0603 (C19666, +-10%) | OK (0402 in the reference) |
| 4 | 2nd VOUT cap | 4.7 uF at a DVDD pin, away from LX/COUT (DS 6.3.8.1 p412) | none | **NG -> fixed**: C30 4.7 uF at DVDD pin 32 |
| 5 | VREG_FB | fed from COUT output, not routed under LX (DS 6.3.8.1; pin table: "connect to DVDD") | pin 65 = +1V1 | OK (routing ?) |
| 6 | VREG_PGND | to main GND at a single point, high-current loop small (HDG 2.1 p5; DS 6.3.8.1) | pin 62 = GND | OK schematic / layout ? |
| 7 | VREG_AVDD | RC 33 Ohm + 4.7 uF (HDG 2.1 p7; DS 6.3.8.1) | R1 33 Ohm + C7 4.7 uF | OK |
| 8 | DVDD caps | 100 nF per power pin (HDG 2.2.1 p8) | DVDD 10/51: 100 nF each, DVDD 32: none | **NG -> fixed** (pin 32 now has the 4.7 uF C30) |
| 9 | IOVDD caps | 100 nF per pin, 8 pins (HDG 2.2.1) | 6 caps for 8 pins | **NG -> fixed**: C28 (pin 24), C29 (pin 29) |
| 10 | ADC_AVDD | 3.3 V; can share the IOVDD supply; 100 nF (DS 6.1.5 p401; HDG 2.2.1) | pin 59 = +3V3, no cap | **NG -> fixed**: C31. No RC filter (ADC only used as digital) |
| 11 | USB_OTP_VDD / QSPI_IOVDD | 3.3 V; pins 68 and 69 may share one cap (HDG 2.2.1 p8); RP2354 needs QSPI_IOVDD = 3.3 V (DS 14.x p1341) | both +3V3, no cap | **NG -> fixed**: C32 shared |
| 12 | QSPI pins (RP2354B) | internal W25Q16JVWI on the same pads; external pins may stay unconnected (DS 14.3 p1326-1327) | SD0-3/SCLK NC | OK |
| 13 | QSPI_SS / BOOTSEL | 1 kOhm to a button to GND; pull-up not needed (HDG 3.1 p10-11) | R4 1k -> SW2 -> GND, no pull-up | OK |
| 14 | Crystal | ABM8-272-T3 12 MHz, 15 pF x2, 1 kOhm series on XOUT, IOVDD = 3.3 V (HDG 4 / 4.1 p13-14) | Y1 ABM8-272-T3, C8/C9 15 pF, R2 1k, IOVDD 3.3 V | OK (traces short; placed at XIN/XOUT) |
| 15 | RUN | button to GND (HDG 5.4 p18) | SW1 + R3 10k pull-up | OK |
| 16 | USB | 27 Ohm series close to the chip; 90 Ohm diff over solid GND (HDG 5.1 p15) | R7/R8 27 Ohm locked next to pins 66/67; 1.6 mm board | OK / ? (HDG 90 Ohm example assumes 1.0 mm thickness) |
| 17 | SWD | SWCLK/SWDIO reachable on a header (HDG 5.3 p17) | J7 3-pin (SWCLK/SWDIO/GND) | OK |
| 18 | GPIO 5 V tolerance | "Digital IO (FT)" tolerates 5.5 V only with IOVDD at 3.3 V; ADC pads are not FT (DS 14.8.2.1 Table 1673 p1331) | GPIO40-47 3.3 V only (test); cart 5 V is switched on by CART_EN after boot | OK (power-down order ?) |
| 19 | LDO | NCP1117 with 10 uF in/out (HDG 2.2 p7-8) | C1/C2 10 uF | OK |
| 20 | Regulator layout | follow Fig. 25/26 exactly, B.Cu GND under the regulator (DS 6.3.8 p409-411) | approximation (L1/C5-C7/R1 locked near pins 61-65) | ? (copy the Pico 2 / Minimal KiCad layout) |

## Inductor replacement

DS 6.3.8.2-3 requires a polarity-marked part and recommends the AOTA-B201610S3R3-101-T. HDG 2.1 states that no other suitable polarity-marked 0806 part could be found.

Unmarked 2016 3.3 uH parts in LCSC stock do not meet the requirement. For example, SOREDE SNR.201610.SYB3R3MT00 (C5122813) has DCR 294 mOhm and Isat 1.05 A, so it fails anyway.

**Conclusion:** keep the AOTA-B201610S3R3-101-T. It is 0 in stock at LCSC (C42411119) but stocked at other distributors (Symmetry, about 8.1k; Octopart lists about 9k).
- Source it via JLC Global Sourcing / consignment, or hand-place it.
- No order has been placed.

## Uncertain / not done
- L1 land pattern: we use a Murata DFE201610P land. It has not been compared with the Abracon drawing, and the polarity dot orientation versus DS Fig. 26 is not checked.
- The regulator layout is not a copy of the Pico 2 layout.
- USB impedance on 1.6 mm FR4.
- 0603 instead of 0402 caps; ESL is assumed to be within 6 nH.
- ADC_AVDD has no RC filter. Fine as long as the ADC is not used for measurement.
- The cap placement for pins 24/29/32 is approximate. Pin 29 is served from the left column.

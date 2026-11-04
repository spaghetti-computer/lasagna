# LASAGNA2354 (ラザニア2354) Rev.C plan: RP2354B direct-drive (PROPOSAL, nothing validated)

Rev.C replaces the Pico 2 module and the 16-chip Rev.B latch farm with a bare
RP2354B (QFN-80, 48 GPIO, 2 MB stacked flash). The parts are meant for
self-reflow with a stencil on a hotplate; JLC PCBA is optional. This is a
planning document. There is no KiCad project for Rev.C yet.

## 1. RP2354B facts (RP2350 datasheet, https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- RP2354B: QFN-80 10x10, 48 GPIO, 8 analogue inputs, 2 MB stacked flash.
- QFN-80 ADC pins: GPIO40-47 = ADC0-7. These are "Digital IO / Analogue" pads and are **not** fault tolerant.
- GPIO0-39 on QFN-80 are "Digital IO (FT)". From Table 1673: "they will
  tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V". With
  IOVDD = 0 V, only "very little current flows whilst it is below 3.63 V".
  -> The 5 V cart must only be powered while IOVDD = 3.3 V is up. Keep the Rev.B
  P-FET switch and sequence it from firmware.
- Outputs swing to IOVDD (3.3 V). Default drive is 4 mA (up to 12 mA programmable).
- Core regulator: on-chip SMPS. VREG_VIN 2.7-5.5 V, VREG_AVDD 3.135-3.63 V.
  It needs an external 3.3 uH inductor on VREG_LX and 4.7 uF in/out caps
  (datasheet reference circuit). Use the Raspberry Pi minimal-design inductor
  part (the datasheet asks for a specific low-DCR, polarity-marked type; verify
  the part number in the RP2350 hardware design guide).
- Clock: 12 MHz crystal on XIN/XOUT. The USB bootloader assumes 12 MHz.
- USB: native USB_DP/DM, 27 ohm series resistors per the hardware design guide.
- Decoupling: 100 nF per IOVDD/DVDD pin plus bulk, per the hardware design guide.
- Erratum E9: the internal pull-down is unusable (we measured >1 ms hold).
  Use the internal pull-up or external pulls only.

## 2. Pin allocation (48/48 used, 0 spare)
A direct, unlatched layout needs about 59 pins: CPU 26 + PPU 24 + 3 status +
/PA13 + 3 CVBS + 4 pad + 1 audio. That does not fit. Rev.C therefore
multiplexes the low address byte with the data byte on each bus. This is
exactly what the real 2C02 PPU does with its external 74LS373.

| GPIO | Signal | Dir (from RP) | Pad | Note |
|---|---|---|---|---|
| 0-7 | CPU AD0-7 | out(addr)/in(data) | FT | to LVC573 #1 D and cart D0-7 |
| 8-14 | CPU A8-A14 | out | FT | direct |
| 15 | CPU R/W | out | FT | |
| 16 | /ROMSEL | out | FT | PIO computes from A15 and M2 |
| 17 | M2 | out | FT | |
| 18 | CPU_ALE | out | FT | LE of LVC573 #1 |
| 19-26 | PPU AD0-7 | out/in | FT | to LVC573 #2 D and cart PD0-7 |
| 27-32 | PPU A8-A13 | out | FT | |
| 33 | /PA13 | out | FT | inverter done in GPIO, no '04 |
| 34 | PPU /RD | out | FT | |
| 35 | PPU /WR | out | FT | |
| 36 | PPU_ALE | out | FT | LE of LVC573 #2 |
| 37 | /IRQ | in | FT | external 10k pull-up to 5 V cart rail is OK (FT) |
| 38 | CIRAM A10 | in | FT | mirroring from cart |
| 39 | CIRAM /CE | in | FT | |
| 40-42 | CVBS DAC b0-b2 | out | ADC, non-FT | 3-bit R-ladder to RCA, as in Rev.B |
| 43 | EXP audio in | ADC3 | non-FT | cart sound pin, via AC coupling + bias, clamp below 3.3 V |
| 44 | I2C0 SDA | i/o | non-FT | to U10 MCP23017 + Grove J9; 4.7k to 3.3 V (superseded the direct pad pins, see 2f) |
| 45 | I2C0 SCL | out | non-FT | |
| 46 | spare (TP G46) | - | non-FT | 3.3 V only |
| 47 | spare (TP G47) | - | non-FT | 3.3 V only |

PIO windows: on RP2350B a PIO block's GPIO base can be 0 or 16.
- CPU state machine: base 0, pins 0-18.
- PPU state machine: base 16, pins 19-39 (IRQ/CIRAM can be read with `in pins` in the same window).
- Video and pads go on the third PIO with base 16 (40-47 are inside 16-47).
- The CPU and PPU groups must be in contiguous runs so that one `out pins,N` sets the whole address.

Dropped compared with Rev.B: the 165/595 chain (pads are direct now), the status
buffer, the decoder, the Johnson counter, and the level translators.

## 3. 5 V interface (honest)
- **Inputs from the cart** (data, /IRQ, CIRAM): all are on FT pins, so no shifter
  is needed (datasheet-backed, conditional on IOVDD = 3.3 V first).
- **Outputs to the cart are 3.3 V CMOS.**
  - TTL-input parts accept them: 74LS VIH(min) = 2.0 V (TI SN74LS datasheets).
    NMOS/TTL-compatible mask ROMs are typically VIH 2.0-2.2 V (generic JEDEC TTL; check each cart).
  - **Risk:** CMOS-input parts on the cart do not accept them reliably.
    - 74HC at 5 V has VIH(min) = 3.15 V (TI SN74HC datasheets), so 3.3 V is only 0.15 V above it, with no margin.
    - Mapper ASICs (MMC1/MMC3 etc.) have VIH that is not documented publicly.
  - Fallback: put 74AHCT541-class buffers (VIH 2.0 V, 5 V out) on the output-only
    lines. This would add 3-4 ICs.
  - The 573 latches run at 3.3 V, so the latched A0-7 are also 3.3 V.
    Using 74AHCT573 at 5 V instead would give 5 V A0-7 at no extra IC count. Use the
    TTL-threshold AHCT version if the 5 V option is chosen (AHCT accepts 3.3 V input).
- The AD pins see 5 V from the cart only while the cart drives data, which is fine on FT pins.
- PIO must release the AD pins (pindirs 0) before /ROMSEL+M2 or /RD asserts, to avoid bus fights.
  Series 33-47 ohm resistors on the AD lines are recommended.

## 4. Timing (nespico/revc.py, tests/test_revc.py)
Margins in ns:

| profile | MHz | CPU M2-low | CPU M2-high | PPU slot |
|---|---|---|---|---|
| measured_style | 150 | 158.5 | 103.2 | 108.5 |
| measured_style | 172 | 163.6 | 108.3 | 121.3 |
| proposed (v3 tricks) | 150 | 171.9 | 116.5 | 141.8 |
| proposed | 172 | 175.3 | 120.0 | 150.3 |

The Rev.B measured profile at 150 MHz was 111.5 / 95.2 / 51.5.
- The model assumes ROM tACC 200/150 ns and LVC573 8 ns.
- The PPU margin about doubles because the second latch load and the status MUX read are gone.
- The clock counts are extrapolated from the Rev.B measurement and are not measured on Rev.C.
- 172 MHz is still preferred.

## 5. BOM (logic ICs: 2)
| Qty | Part | Note |
|---|---|---|
| 1 | RP2354B | Akizuki 131441 ¥280; LCSC C39843328 |
| 2 | 74LVC573A (TSSOP-20) | address latches (or 74AHCT573 at 5 V, see section 3) |
| 1 | 3.3 V LDO, >=300 mA (e.g. AP2112K-3.3 / XC6220) | LCSC/Akizuki not checked |
| 1 | 12 MHz crystal + 2 load caps | per hardware design guide |
| 1 | 3.3 uH inductor + 2x 4.7 uF | VREG |
| 1 | USB-C receptacle + 2x 5.1k CC + 2x 27R | |
| 1 | AO3401A + polyfuse 500 mA + switch/LED | cart 5 V switch carried over from Rev.B |
| ~12 | 100 nF, 3x 10 uF | decoupling |
| 16 | 33 ohm | AD series |
| 3 | 910/470/220 ohm + 75 ohm | CVBS + RCA |
| ~6 | 10k | /IRQ pull-up, pad data pull-ups, BOOTSEL, RUN |
| 2 | buttons | BOOTSEL, RUN |
| 1 | SWD header 3-pin | |
| 1 | Famicom 60-pin slot | footprint still unverified |
| 2 | pad connector (pinout TBD) | |

The prices of passives, LDO, crystal and inductor were not checked.

## 6. Apple II-style layout sketch (100 x 80 mm, 2 layers; F.Cu = horizontal, B.Cu = vertical)
Silkscreen row letters A-C and column numbers 1-6. Every IC has pin 1 at the top-left (same orientation).
```
     x: 10      25      40      55      70      85
 y=8  [USB-C] [LDO][SW/FET/F]      [XTAL]  [RCA][AUD]
       1       2       3       4       5       6
 A 20  .      [U2 573] [U1 RP2354B] [U3 573]  .   [PAD1]
 B 38  .       C C     (QFN, L, caps)  C C     .   [PAD2]
 C 52  [SWD][BOOT][RUN]  [R-pack AD series] [CVBS R]
 y=60-78  ================= Famicom 60-pin slot (edge, x 15..85) ========
```
- U1 sits at B3/B4, with U2 (CPU latch) on the left and U3 (PPU latch) on the right, all 0 deg.
- Use the AD series resistors as the H-to-V crossover so the buses run straight down to the slot.
- A grid-tidy layout is cosmetic. QFN fan-out is the real routing constraint; vias can stay H/V.

## 7. Risks
1. 3.3 V outputs into CMOS mappers or 74HC on the cart (section 3). **This is the biggest risk.** Leave footprints for an optional AHCT buffer board/jumper.
2. FT tolerance needs IOVDD up before the cart 5 V comes up. The power-switch sequencing must be right at boot and when unplugging USB.
3. GPIO40-47 are not FT. Nothing 5 V may reach them: pads must be powered at 3.3 V, and audio must be clamped.
4. 0 spare GPIO. No debug UART, and no $4016 expansion beyond 2 pads. SWD stays available (dedicated pins).
5. QFN-80 0.4 mm pitch reflow with a hotplate: the EP needs a windowed stencil. Inspect for bridges.
6. The timing numbers are model extrapolations.
7. VREG inductor choice: use the part from the design guide. Generic inductors are reported to cause regulator issues.

## 8. Open questions
- 5 V buffering: always on (AHCT573 + 2x AHCT541) or omitted?
- Famicom pad connector type (Famicom expansion DA-15 vs NES 7-pin vs custom)?
- Audio: does the cart sound pin need an ADC, or is it passed through analog to the RCA mixer?
- 5 V latches (74AHCT573 on the cart rail)? This removes risk on A0-7 at no IC cost.


---
## 2b. FINAL (Leo-approved 2026-10-13): every signal driven toward the cart is 5 V CMOS
This section supersedes sections 2, 3 and 5. KiCad project: `revc/`, generated from `revc/design.py`.

### Final IC list: 7 logic ICs (plus RP2354B and an LDO)
| Ref | Part | LCSC | Function |
|---|---|---|---|
| U1 | RP2354B | C39843328 | MCU, 48 GPIO, 2 MB flash in package |
| U2 | 74AHCT573PW | C282327 | CPU A0-7 latch (LE = CPU_ALE), 5 V outputs |
| U3 | 74AHCT573PW | C282327 | PPU A0-7 latch (LE = PPU_ALE) |
| U4 | 74AHCT245PW | C173388 | CPU D0-7. A side = cart, B side = MCU. DIR = R/W (H = cart->MCU). **OE_N = /M2 GPIO**, so it is enabled only while M2 is high |
| U5 | 74AHCT245PW | C173388 | PPU D0-7. DIR = /WR (H = read). OE_N = PPU_DEN_N (GPIO33) |
| U6 | 74AHCT541PW | C84548 | CPU A8-A14 and R/W |
| U7 | 74AHCT541PW | C84548 | /ROMSEL, PA8-PA13, /WR |
| U8 | SN74AHCT540PWR | C7626 | inverting: /M2 GPIO -> M2, PA13 -> /PA13, RD -> /RD (5 inputs unused, tied to GND) |
| U9 | NCP1117ST33T3G | C26537 | 3.3 V LDO (HDG minimal design) |

### Data-write decision
Writes go through the 5 V AHCT245 transceivers (correctness first). Writes to 74HC-based mappers
(VIH 3.15 V) or CMOS mapper ASICs therefore get a full 5 V level. On reads, the 245 drives 5 V into the
FT pins. That is allowed by the datasheet only while IOVDD = 3.3 V, and the power sequencing below guarantees it.

How the pins still fit:
- DIR comes from the existing R/W and /WR GPIOs.
- The CPU 245 OE_N is the same GPIO as M2: the MCU outputs /M2, and U8 inverts it for the cart.
- /PA13 is made by U8 from PA13, so its GPIO is freed.
- The audio ADC was dropped, which frees one more GPIO.
- The two freed GPIOs become PPU_DEN_N (33) and CART_EN (43).
- Result: **48/48 GPIO, 0 spare.**

### GPIO map (final)
| GPIO | Signal |
|---|---|
| 0-7 | CPU AD0-7 (33R -> U2 D and U4 B) |
| 8-14 | A8-14 -> U6 |
| 15 | R/W -> U6 and U4 DIR |
| 16 | /ROMSEL -> U7 |
| 17 | /M2 -> U8 (M2) and U4 OE_N |
| 18 | CPU_ALE |
| 19-26 | PPU AD0-7 (33R -> U3 and U5) |
| 27-32 | PA8-13 -> U7 (PA13 also -> U8 -> /PA13) |
| 33 | PPU_DEN_N |
| 34 | RD (active high) -> U8 -> /RD |
| 35 | /WR -> U7 and U5 DIR |
| 36 | PPU_ALE |
| 37 | /IRQ in (FT) |
| 38 | CIRAM A10 in (FT) |
| 39 | CIRAM /CE in (FT) |
| 40-42 | CVBS DAC |
| 43 | CART_EN |
| 44 | I2C_SDA (I2C0) |
| 45 | I2C_SCL (I2C0) |
| 46 | SPARE_GP46 (TP) |
| 47 | SPARE_GP47 (TP) |

### Power sequencing
1. VBUS -> polyfuse -> +5V_LOGIC -> NCP1117 -> +3V3 (IOVDD).
2. All 5 V logic is on **+5V_CART**, which is switched by an AO3401A. Its gate is pulled up to 5 V (off).
   CART_EN (GPIO43, 10k pull-down) drives a 2N7002 that turns the FET on. Firmware asserts it only after IOVDD is up.
3. All latch and buffer OE_N pins share OUT_OE_N: 10k pull-up to +5V_CART, pulled low by a second 2N7002
   through a 10k/100nF RC (~1 ms after cart power). The outputs are therefore Hi-Z while VCC ramps.
4. The 245 OE_N nets (/M2, PPU_DEN_N) have 10k pull-ups to +3V3, so both are off at reset.
5. Cart-side idle pulls:
   - pull-ups on /ROMSEL, R/W, /RD, /WR, /IRQ and CIRAM /CE
   - pull-downs on M2 and CIRAM A10
6. **Open:** when USB is unplugged, +3V3 decays while the cart/logic rail also decays. The FT spec
   (IOVDD = 0 V allows 3.63 V max) can be exceeded briefly. A supervisor or a faster discharge on +5V_CART is a candidate fix.

### Timing impact (not yet in revc.py)
- AHCT541/573 tpd is about 8.5 ns @50 pF, and the 245 is 3.5 ns typ. That adds roughly 10 ns to each path on top of the latch 8 ns already modelled.
- The worst margin is still about 90 ns at 150 MHz. This is an estimate, not measured.

### Board (revc/)
- Size and layers: 100 x 52 mm "stick", 2 layers. One IC row "A", columns 1-7, all ICs at 0 deg with pin 1 top-left, and a decoupling cap next to each IC.
- Top band: USB-C, LDO, power switch, RP2354B with its HDG support parts, buttons, SWD and RCA.
- Bottom edge: cart slot (2x30 placeholder). Above it: the 2x20 test-point header and the two 1x7 pad headers.
- Routing intent: F.Cu vertical, B.Cu horizontal (silk note). Freerouting does not strictly enforce this.

---
## 2c. Steve review fixes (2026-10-13, Leo-approved). PROPOSAL, not validated
- **P1 floorplan.** From the top: slot (top edge) -> keepout -> row A of 7 logic ICs at y=18
  (U2 U4 U6 | U8 | U7 U5 U3, horizontal, same orientation) -> RP2354B at y=38 -> front row at y=52
  (J4, SW1 RUN, J7 SWD, SW2 BOOTSEL, J5) -> J8 2x20 at y=59.5.
  USB-C (left) and RCA (right) are at y=32 on the short edges.
- **P2.** These parts are placed and locked relative to U1:
  - L1, C5 (VIN), C6 (DVDD out) and C7 + R1 (VREG_AVDD RC) sit right above VREG pins 61-65.
  - Y1 is 8.6 mm below XIN/XOUT (pins 30/31), with C8/C9 15 pF and R2 1k next to it.
  - A B.Cu rule area under Y1 bans tracks and vias.
  - The IOVDD/DVDD 100 nF caps sit next to pins 5/10/15/41/50/51/60/76.
  - Not yet checked against the HDG reference layout geometry: L1 polarity dot orientation and the DVDD/FB trace topology.
- **P3.**
  - GPIO40-47 carry: CVBS DAC (3.3 V out), CART_EN (to 2N7002 gate + 10k pull-down) and I2C0 SDA/SCL plus 2 spares (all 3.3 V; the pads moved to U10 MCP23017).
  - No 5 V-driven net reaches them. This is checked by `tests/test_revc.py::RevCDesignTest`.
  - Power-up defaults:
    - OUT_OE_N: 10k to +5V_CART, plus the RC-delayed 2N7002.
    - U4 OE_N (/M2) and U5 OE_N (PPU_DEN_N): 10k to +3V3 (off).
    - CART_EN: 10k to GND (cart off).
  - Added 10k pull-ups to +3V3 on the 245 DIR nets G_RW and G_WR_N, so the default direction is read.
- **P4.**
  - The U8 74AHCT540 inversion is intentional:
    - GPIO17 is /M2 and drives U4 OE_N directly, so U4 is enabled only while M2 is high. U8 inverts it to cart M2.
    - PA13 -> /PA13 is a real inverter.
    - RD (active high) -> /RD.
  - Firmware must program these polarities. PIO outputs /M2, RD and PA13 non-inverted; there is no GPIO OUTOVER.
  - **DIR-flip contention guard:** DIR (R/W, /WR) may change only while the matching 245 OE_N is high.
    - CPU: R/W changes only during M2 low, when /M2 is high and U4 is off.
    - PPU: assert PPU_DEN_N high, then change /WR (DIR), then wait at least 1 PIO clock, then enable.
    - The 33R series resistors on the AD lines limit current from any residual overlap. Not measured.
- **P5. Soft start.**
  - Q2 now drives the AO3401A gate through 1k (CART_G_DRV -> CART_G).
  - A 100 nF gate-source cap (C25) ramps the gate with tau of about (10k||1k)*100nF, roughly 90 us. Raise C25 for slower inrush.
  - The cart rail has C3 10 uF + C26 100 nF (HF bypass).
- **P6. Decoupling and GND pour.**
  - Each TSSOP gets its own 100 nF (C10-C16), locked on the same side next to VCC pin 20.
  - A B.Cu GND pour zone is defined over the whole board but left unfilled; the slot keepout bans pour in the slot area.
- **P7. Edges and parts.**
  - USB-C mouth overhangs the left edge by 0.5 mm. That leaves a silk_edge_clearance warning on purpose.
  - RCA pads sit 0.55 mm inside the right edge. The RCA footprint itself is still unverified.
  - J3: NESdev (https://www.nesdev.org/wiki/Cartridge_connector and Famicom_cartridge_dimensions) confirms 2x30, 2.54 mm pitch and a 1.2 mm thick cart PCB. Pins 1-30 are on the label side.
    - The real slot's row spacing, peg holes and body outline are **not verified**. The footprint is still a 2x30 2.54 mm header placeholder.
    - Pick an actual 60-pin 2.54 mm edge connector, for example the AliExpress "Famicom 60-pin" parts mentioned on the NESdev forum, and draw its footprint from its datasheet.
  - R7/R8 (USB 27R) are locked next to U1. R90-R92 (CVBS DAC) are locked next to J6. All other resistors stay off-board for Quilter.
- **Availability (JLCPCB pages, 2026-10-13). All are Extended parts.**

| Part | LCSC / JLC part | JLC status |
|---|---|---|
| RP2354B | C39843328 | Extended (LCSC stock ~3.2k) |
| SN74AHCT573PWR | C141311 | JLC stock 1830 (replaces Nexperia C282327, which had JLC stock 0) |
| 74AHCT245PW | C173388 | 273 |
| 74AHCT541PW | C84548 | ~20.9k |
| SN74AHCT540PWR | C7626 | 1000 |
| NCP1117ST33T3G | C26537 | LCSC ~105k |
| AOTA-B201610S3R3-101-T (inductor) | C42411119 | LCSC stock 0 |

  The inductor has no stock, so a substitute is needed. Not chosen yet.

## 2d. Aesthetic pass (Leo: "make it look nice")
- Black mask, white silk, HASL lead-free. Recorded in the stackup and in revc/FAB_NOTES.md.
- Row A is exactly mirrored about x=50, with U8 on the centreline. Each IC carries its coordinate (A1..A7) on silk;
  the refdes moved to fab, with a cross-reference table in FAB_NOTES.md (removed from the silk).
- USB-C and RCA body centres are both at y=32.0.
- The 33R arrays are hand-placed and locked. The other misc resistors stay off-board for Quilter.
  R90..R92 moved to a row under the RCA, because the PPU array was in their old spot.
- GND pour is bottom-only. Routing guidelines are in revc/README.md.

## 2e. Test points + production finish
- J8 is removed. 22 THT test points (TP1..TP22, B side) are in one 3.81 mm-pitch row on the front edge.
  CPU signals are on the left, power in the centre and PPU signals on the right, mirrored.
- R3 corners, mounting-hole keep-out rings, 3 fiducials, a JLC order-number spot, the wordmark + REV.C, and a minimal back block (LASAGNA2354 REV.C / MADE IN KOBE).
- TPs are THT (2.0/1.0 mm) on the B side, with back-silk labels only.
- Net classes (Power/Signal/USB_90R) and a JLC .kicad_dru are set.
- Board height is kept at 62 mm, so there is margin under the TP labels.

## 2f. Controller pads via an I2C expander + Grove
- U10 MCP23017-E/SS (SSOP-28, LCSC C506653, about 995 in stock on 2026-10-13).
  - Address 0x20 (A2..A0 = GND). RESET has a 10k pull-up. INTA/INTB are NC.
  - Placed at grid B2 under column 2 in the same rotation as row A, with C27 100 nF at VDD (pin 9).
- Supply: U10 and both pads run at **3.3 V**.
  - The pads use a CD4021 shift register (3-15 V), so they work at 3.3 V and no level shifting is needed.
  - 5 V pads would push 5 V into the MCP23017 inputs while it runs at 3.3 V. Not done.
- Pins: GPA0 = PAD_CLK (out), GPA1 = PAD_LATCH (out), GPA2/GPA3 = PAD1_D/PAD2_D (inputs, internal 100k pull-ups on so an unplugged pad reads 1).
- Software reads both pads about once per frame: latch pulse, then 8x (read GPA2/3, clock pulse).
  - That is about 18 I2C register writes plus 8 reads at 400 kHz, roughly 1.5-2 ms per frame on the core-1 side. It is not timing-critical.
- I2C0 on GPIO44 (SDA) / GPIO45 (SCL). 4.7k pull-ups to 3.3 V (R, off-board for Quilter).
- Grove J9 (HY2.0-4P-WT, LCSC C722729) on the left edge under the USB-C, with an "I2C" silk label.
  - Pinout: 1 GND, 2 3V3, 3 SDA, 4 SCL.
  - The footprint is a JST PH SMD right-angle stand-in: UNVERIFIED against the HY2.0 drawing.
- Freed GPIOs: 4 (44-47). 2 are used for I2C, so **2 are spare: GPIO46, GPIO47**, exposed as TP "G46"/"G47" in the centre of the TP row.
  - The TP row is now 24 pads at a 3.5 mm pitch (was 22 at 3.81).
- To make room for J9, USB-C and RCA both moved to y=30.5, which keeps them at matching heights.
  The CART LED moved under the RCA; the column numbers moved 1 mm up.

## 2g. HDG audit (see revc/HDG_AUDIT.md)
- Fixed: one 100 nF per supply pin. Added C28 (IOVDD 24), C29 (IOVDD 29), C31 (ADC_AVDD) and C32 (USB_OTP_VDD + QSPI_IOVDD), plus the 2nd 4.7 uF VOUT cap C30 at DVDD pin 32.
- Inductor: keep the AOTA-B201610S3R3-101-T, because a polarity-marked part is required. It is out of stock at LCSC, so it will need Global Sourcing.

## 2h. Minimal copy, power-down, sourcing (2026-10-13)
- **VREG and crystal copied from the RP2350 Minimal.** Each part keeps its exact offset from the U1 pins.
  - VREG pins move from QFN-60 46–52 to QFN-80 61–67, a shift of (+1.0, −1.5) mm.
  - XIN/XOUT move from 21/22 to 30/31, a shift of (+0.6, +1.5) mm.
  - Footprints copied unchanged: L1 AOTA, C5/C6/C7, R1, R7/R8, Y1/C8/C9/R2, DVDD C29/C30 (0402).
  - L1 pad 1 (dot) = +1V1. These positions are locked: do not move them by hand.
- **Power-down.** NCP1117 dropout is about 1.1 V, so +3V3 falls below 3.0 V once 5 V drops to about 4.1 V. Below that, FT pins with cart 5 V on them are outside their rating.
  - Fix: U11, an XC61CN3002 (3.0 V open-drain detector, C2456348), forces CART_EN low.
  - That turns the cart power FET off and takes the AHCT outputs Hi-Z.
  - GPIO43 (CART_EN_G) drives CART_EN through a 1k so it cannot fight U11.
- **Sourcing.** Anything not at LCSC comes from Akizuki and is hand-soldered (see HAND_ASSEMBLY.md).
- **J3 TBD.** No purchasable slot with a drawing was found.
  - Known: 2.54 mm pitch, 2×30, 1.2 mm cart PCB, card-edge depth about 10.7 mm.
  - Candidates: ToToTEK ($4, in stock); ZedLabz (sold out).
  - Final footprint waits until the real part is in hand and measured.
- **J9 Grove.** The HY2.0-4P drawing has no land pattern, so the JST PH SM04B footprint is an approximate stand-in (TBD).
- **4.7k.** C23162 0603 is a JLC Basic part (verified).

## 2i. J3 = Hirose CR22A-60D-2.54DS(70) (2026-10-13)
- Leo already owns this part. The footprint comes from the Hirose CR22 catalog D49647, pages A4/A6:
  - 2×30 rows, 2.54 mm pitch, 5.08 mm row spacing, holes ø0.8 (+0.2/0); drill 1.0, pad 1.7.
  - Body A 84.84 × D 9.5, card opening B 78.74, height 16.5. The A suffix means no mounting holes.
- Pin mapping: pad n = cart pin n (NESdev). Pins 1–30 are the label-side row (y = 7.8); 31–60 are the row 5.08 mm nearer the top edge. Pin n faces pin n+30.
- The slot is centred on x = 50, and the keepout is a 1.2 mm band below the real body. H1/H2 moved to x = 3.7/96.3 to clear the body.
- The connector is rated for 1.6 mm cards, while a Famicom cart is 1.2 mm. Check the fit and contact pressure on the real part.
- L1 stays AOTA. NLV32T-3R3J-EF fails DCR, current, shielding and polarity (see HAND_ASSEMBLY.md). Grove keeps the approximate footprint.

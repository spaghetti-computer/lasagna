# Pico 2 board plan and external-logic options — Rev.B proposal (draft)

**Status: proposal only, not a sign-off.** This revision proposes a *Rev.B* GPIO allocation that adds composite (CVBS) video, a shift-register chain for the Famicom 15-pin expansion port / controllers, and USB video/audio output, under the user's cost constraints (no second MCU, no FPGA, no LCD). Nothing here has been built, simulated at gate level, run as PIO, or measured. The Rev.A logical candidate in [`rev-a-circuit-spec.md`](rev-a-circuit-spec.md) and [`rev_a_logic/`](rev_a_logic/) is **not** updated by this document; if Rev.B is accepted, those files, their validators and the KiCad schematic must be revised separately. All prices are rough, unverified estimates.

## Confirmed project constraints (unchanged)

- Target is a standard, non-wireless Raspberry Pi Pico 2 (RP2350A package, 30 GPIOs total).
- **GP26–GP28 are reserved for ADC0–ADC2** and carry no digital cartridge, video or serial signals.
- **GP29 (ADC3) is the Pico 2's VSYS/3 monitor**; GP23/GP24/GP25 are on-board functions. None are available.
- Digital budget: **GP0–GP22 = 23 pins**. No RP2350 pad connects directly to a cartridge or expansion-port 5 V signal.

| Resource | Count | Project treatment |
| --- | ---: | --- |
| GP0–GP22 | 23 | Digital GPIO budget |
| GP26–GP28 | 3 | ADC0–ADC2, analog only (GP26 = cartridge audio return candidate, as in Rev.A) |
| GP29 | 1 | Pico 2 VSYS monitor, never routed |

## New requirements from the user (2026-10-12)

Goal: lowest cost. No second MCU, no FPGA, no LCD.

1. **Video:** CVBS composite via PIO + resistor-ladder DAC (3–4 GPIOs); **USB video** using a compact custom protocol (6-bit palette indices + frame diffs) to a host viewer; optional low-fps UVC as a bonus mode.
2. **Audio:** USB Audio Class (TinyUSB). Consider an analog PWM + RC output (1 GPIO) beside CVBS.
3. **Expansion port / controllers:** Famicom 15-pin expansion port and controllers via 74HC165 (in) + 74HC595 (out) on a shared serial chain.
4. **Cartridge bus:** move address bits into latches/transceivers as needed.
5. **Core split:** core0 = cartridge bus + emulation; core1 = video/audio output (CVBS encode, USB streaming).

## Pin budget result (headline)

Rev.A already used all 23 pins (16 data + 6 control/strobe + 1 audio PWM). Adding a 3-pin CVBS DAC and a 3–4-pin serial chain as *dedicated* GPIOs would need **29–30 pins: 6–7 over budget.** Rev.B fits in **23/23 with 0 spare** by:

- folding CPU R/W, the /ROMSEL qualifier and PPU /RD vs /WR selection into **latched control bits** loaded over the existing data lanes (saves 2 pins: Rev.A GP17, GP19 become latch outputs; GP18 becomes a single PPU strobe);
- driving the 165/595 chain from **spare bits of the CPU control latch** and returning its serial output through the existing Rev.A status MUX (0 dedicated GPIOs);
- dropping the dedicated APU PWM pin (Rev.A GP22). Audio leaves via USB UAC; the cartridge pin 45 audio input is biased instead of driven (see risks);
- limiting CVBS to a **3-bit** DAC (not 4).

A dedicated analog-audio PWM pin, a 4th DAC bit, or a dedicated serial chain all need a pin freed somewhere else. Options are listed under *Open questions*.

## Proposed Rev.B GP0–GP22 allocation

| GPIO | Signal | Dir | Path / notes |
| --- | --- | --- | --- |
| GP0–GP7 | CPU_D0–D7 | bidir | As Rev.A: AHCT244 (TX) / LVC244A (RX). **Also loads** CPU addr-lo, addr-hi and CPU control latch bytes while both transceivers are Hi-Z |
| GP8–GP15 | PPU_D0–D7 / status | bidir | As Rev.A: TX/RX buffers + LVC257A status MUX. Also loads PPU addr-lo / addr-hi (incl. control bits). Status MUX B side now also returns `SR_QH` (165 serial out) |
| GP16 | CPU_M2 | out | Via AHCT control buffer, gated by `BUS_RUN` (as Rev.A). Rising edge also resets the CPU latch phase counter |
| GP17 | CPU_ALE | out | Steps a 2-bit phase counter (74HC74 or '161) decoded by 74HC139 into three latch clocks: addr-lo → addr-hi → CPU control latch. Counter cleared while M2 high |
| GP18 | PPU_ALE | out | Toggles a phase flip-flop: addr-lo → addr-hi (hi byte bits 6–7 = PPU control bits). Cleared by PPU_STB |
| GP19 | PPU_STB | out | Single active-low timing strobe; gated by latched `PPU_RD_SEL` / `PPU_WR_SEL` (74AHCT00/32) into cartridge PPU /RD or /WR. Never both: select bits are mutually exclusive by decode, still to be proven in the Boolean validator |
| GP20 | CVBS_B0 (LSB) | out | 910 Ω to CVBS node |
| GP21 | CVBS_B1 | out | 470 Ω |
| GP22 | CVBS_B2 (MSB) | out | 220 Ω |
| GP26–GP28 | ADC0–ADC2 | analog | Reserved; GP26 cart audio return (pin 46) as in Rev.A, after conditioning |
| GP29 | VSYS/3 | — | Internal, not routed |

**Spare digital GPIOs: 0.** The three CVBS pins are contiguous so one PIO `out pins, 3` covers them; GP0–GP7 and GP8–GP15 stay contiguous for 8-bit `out`/`in`.

### Signals moved to external logic and how

| Signal(s) | Rev.A | Rev.B proposal |
| --- | --- | --- |
| CPU A0–A7 | latch from CPU lane | unchanged (74AHCT574, phase 0) |
| CPU A8–A14, A15 | latch from CPU lane | addr-hi latch (phase 1); bit 7 = A15, used only to qualify /ROMSEL = NAND(A15, M2) |
| CPU R/W | GP17 | **CPU control latch** bit 0 (phase 2). Must be valid before M2 rises; the phase order guarantees it is loaded before M2 |
| CPU-lane direction intent | decoded from GP17 | derived from latched R/W AND M2 (same equations as Rev.A, new source) |
| Expansion `SR_CLK`, `SR_LD`, `SR_SER` | — | **CPU control latch bits 1–3**, see below |
| CPU control latch bits 4–7 | — | spare (candidates: debug LED, CIRAM override, cartridge power enable — open) |
| PPU A0–A7 | latch | unchanged |
| PPU A8–A13 | latch | addr-hi bits 0–5 |
| PPU /RD, /WR | GP18, GP19 | addr-hi bits 6/7 = RD_SEL / WR_SEL, timed by GP19 PPU_STB |
| /IRQ, CIRAM A10, CIRAM /CE | status MUX on PPU lane | unchanged; plus `SR_QH` on a free MUX channel |
| APU audio PWM → pin 45 | GP22 | removed; pin 45 biased to mid-rail through a resistor; mixing done digitally (see risks) |

### Serial chain for the expansion port and controllers

The user decided on 74HC165 (in) + 74HC595 (out) on a shared clock/latch/data chain. Dedicating 3–4 GPIOs to it does not fit, so Rev.B clocks it **from the CPU control latch**, which is rewritten every CPU cycle anyway (~559 ns):

- `SR_LD` (shared): low = 165 parallel load; its rising edge = 595 RCLK (output update). One pin serves both.
- `SR_CLK`: one edge per CPU cycle at most → one shifted bit per ~1.1 µs.
- `SR_SER`: data into the 595 chain.
- `SR_QH`: the 165 chain output, read back through the PPU-lane status MUX in idle PPU time (5 V → LVC257A input, as for /IRQ).

A 16-bit exchange (2×165, 1–2×595) takes ~35 CPU cycles ≈ 20 µs. That runs continuously in the background, so input state is ≤ ~20 µs old, far faster than the 60 Hz polling games do. The emulator serves $4016/$4017 from the mirrored state. Expansion port OUT0–OUT2 and the controller /OE (clock) lines come from 595 outputs. This is emulated latency, not cycle-exact port behaviour. Peripherals that need precise timing on the $4016/$4017 clock edges (light gun timing, some keyboards, the Famicom Data Recorder) may not work. **Open.**

Alternative with zero GPIOs and fewer chips: decode CPU latched $4016/$4017 locally and use a 74HC574 (out) plus 74HC541/368 (in) on the CPU data lane, which is close to what the real console does. This is listed as an option because it differs from the user's 165/595 decision.

## CVBS video

### DAC resistor values (rationale)

The target is an NTSC-like composite into a 75 Ω load: sync tip 0 V, blank ≈ 0.29 V, white ≈ 1.0 V, with chroma swinging up to ~1.2 V. For an N-bit binary-weighted ladder driven from 3.3 V GPIOs, size the parallel source conductance so full-scale into 75 Ω ≈ 1.2 V:

`Vfs = 3.3 · Gs / (Gs + 1/75) = 1.2 V → Rs ≈ 131 Ω`, split 4:2:1 → 229 / 459 / 918 Ω → E24 **220 / 470 / 910 Ω**.

Calculated output levels into 75 Ω (ideal GPIO, 3.3 V, no tolerance):

| Code | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V | 0.00 | 0.17 | 0.33 | 0.51 | 0.71 | 0.88 | 1.04 | 1.22 |

Suggested mapping: sync = 0, blank/black = 2, white ≈ 6, chroma = ±1–2 codes around the luma code. Source impedance is ≈ 129 Ω, not 75 Ω, so back-termination is mismatched. That is acceptable for short cables, and reflections and level errors must be checked on a real TV. The MSB pin sources ≈ 12 mA in the worst case, so GPIO drive strength must be set to 12 mA and the output-high droop measured. A one-transistor emitter-follower buffer (~10–20 JPY) is a fallback. A 1 nF-ish reconstruction cap / simple LC filter is open.

### Timing

- 4×fsc sampling: 14.318 MHz = 157.5 MHz / 11. A sys clock of **157.5 MHz** (a mild overclock over the 150 MHz nominal) gives an exact integer divider. Alternatively, 6×fsc = 21.477 MHz needs a 171.8 MHz sys clock. The NES PPU itself uses 12 phases at 21.477 MHz, so this would match NES hue phases better. Either choice changes the bus-timing assumptions (the host model assumes 150 MHz).
- At 4×fsc one line is 910 samples. At 3 bits per sample, 10 samples pack per 32-bit word ≈ 91 words/line, fed by DMA.
- With 3 bits, chroma amplitude/phase resolution is coarse, and NES palette fidelity will be visibly worse than real hardware. A 4th bit needs one more contiguous pin (see *Open questions*).

## USB output

- **Primary:** vendor/bulk (or CDC) custom stream: 6-bit palette index per pixel, frame-diff (changed runs/tiles) + periodic keyframes. A raw keyframe is 256×240×6 bit ≈ 46 KB; at an assumed ~0.8–1.0 MB/s usable Full Speed bulk payload (not measured), a full keyframe costs ~1 frame time. Scrolling games defeat simple diffs, so the protocol must tolerate frame drops/decimation. **Not measured.**
- **Audio:** UAC1 (TinyUSB), e.g. 48 kHz mono 16-bit = 96 KB/s isochronous, which competes with video bandwidth. Rate-matching between the emulated APU (~60.1 Hz NTSC frame) and USB SOF is needed.
- **Bonus:** low-fps UVC (e.g. MJPEG/uncompressed at a few fps). RAM and CPU cost on core1 is unknown, so treat it as optional.
- Composite USB device (vendor + UAC [+ UVC] + dumper interface) descriptor complexity is a firmware risk.

## Core / PIO / DMA allocation (proposal)

| Resource | Use |
| --- | --- |
| core0 | 6502 + PPU emulation, cartridge bus producer (pushes PIO FIFOs directly, no DMA, to minimise latency), status/IRQ sampling, serial-chain bit stepping via control-latch bytes |
| core1 | CVBS line encoder (palette index → composite samples), USB TinyUSB stack, video diff encoder, UAC audio |
| PIO0 SM0 | CPU bus engine (M2, CPU_ALE, GP0–7) |
| PIO0 SM1 | PPU bus engine (PPU_ALE, PPU_STB, GP8–15 incl. status reads) |
| PIO0 SM2–3 | spare (e.g. split status sampler) |
| PIO1 SM0 | CVBS sample output (GP20–22) |
| PIO1 SM1–3, PIO2 SM0–3 | spare (bring-up loopback, logic-analyzer test patterns, future analog-audio PWM if a pin is freed) |
| DMA | CVBS: 2 channels (ping-pong/chained line buffers). Optional: 1–2 for PPU fetch lists or audio. ≤ ~5 of 16 channels; USB uses its own DPRAM |

The RP2350A has 3 PIO blocks × 4 SMs = 12 SMs and 32 instruction slots per block. The proposal uses ~3 SMs, so SM count is not the constraint. **Instruction memory** for the CPU and PPU engines sharing PIO0 (32 slots) may be. Splitting them across PIO0/PIO2 is a fallback.

RAM (520 KB): two 6-bit-index framebuffers at 1 byte/pixel ≈ 123 KB, CVBS line buffers < 2 KB, USB/audio buffers small. This looks feasible on paper.

## Timing / bandwidth risks

1. **CPU cycle budget with three latch loads.** One CPU cycle (~559 ns) must contain: 3 × (drive lane + ALE pulse + latch setup/hold, ~3–4 PIO instr each at 6.3–6.7 ns) ≈ 60–90 ns, plus transceiver turnaround and M2 high phase with cartridge ROM access (often 120–200 ns parts) and data sampling. This is plausible on paper but tighter than Rev.A (2 loads). Skipping unchanged bytes is not possible with a fixed phase counter. A resettable/addressable phase selector would allow it at extra logic cost.
2. **PPU slot budget.** Each 2-dot fetch slot is ~372 ns and requires 2 address loads + strobe + CHR access + sample, and the status/SR_QH read must squeeze into idle time. During rendering, nearly all 170 slots/line are busy, so status reads may only fit in HBlank or by stealing slot slack. /IRQ latency then becomes up to ~one scanline unless measured otherwise. The existing host model assumes a 180 ns PPU deadline and 12-clock transactions; both need re-running with this sequence.
3. **Glitches on decoded latch clocks.** A counter + '139 decode can glitch on transitions. Use a Gray/Johnson sequence or a synchronous enable, and verify with a logic analyzer. M2 must never glitch (mapper IRQ counters such as MMC3/M2-based ones count it).
4. **Clock choice coupling.** 157.5 MHz (CVBS-exact) vs 150 MHz (model baseline) vs 171.8 MHz (6×fsc). All bus PIO timing scales with it.
5. **Core1 load.** CVBS encoding at 14.3 MS/s (~910 samples/line, 15.7 kHz) plus USB diff encoding plus UAC must keep up without starving DMA. Not benchmarked.
6. **Shared-pin contention.** The CPU/PPU lanes now carry four kinds of traffic (address, control, data, status). All of them still need the Rev.A break-before-make guarantees, re-proven for the new control sources.
7. **Expansion audio.** Without the Rev.A PWM feed to pin 45, carts that pass pin 45 → 46 return silence, which is fine for digital mixing. Carts with expansion audio (VRC6, VRC7, N163, FDS RAM adapter, etc.) return only their own channel via GP26, and the mix ratio and filtering must be emulated. Whether a biased, undriven pin 45 is safe for all mixer circuits is unverified.
8. **CVBS drive.** 12 mA per pin, 3.3 V rail noise → video noise, and composite colour accuracy with 3 bits are all unmeasured.
9. **USB bandwidth.** Video diff + UAC + optional dumper traffic share Full Speed. Worst-case scrolling frames are not characterised.

## Rough BOM delta vs Rev.A (per board)

**Rough estimates in JPY, not looked up**: typical hobby-retail order of magnitude only. Verify at Akizuki/Marutsu/LCSC/Digi-Key before any ordering decision.

| Part | Qty | Purpose | Rough JPY |
| --- | ---: | --- | ---: |
| 74AHCT574 (or HCT) | 1 | CPU control latch (R/W, SR_CLK/LD/SER, spares) | ~50–100 |
| 74HC74 (or 74HC161) | 1 | CPU 3-phase counter (PPU phase FF may reuse a half) | ~30–60 |
| 74HC139 | 1 | Phase → latch-clock decode | ~30–60 |
| 74HC165 | 2 | Expansion/controller inputs (16 bits) | ~60–120 |
| 74HC595 | 1–2 | Expansion OUT0–2, controller clocks | ~30–120 |
| Resistors 220/470/910 Ω, 1 % | 3 | CVBS DAC | ~10–30 |
| RCA jack (video) | 1 | CVBS out | ~50–100 |
| 15-pin D-sub female (expansion port) | 1 | Expansion port | ~150–400 |
| Controller connectors | TBD | Depends on open question (Famicom hardwired vs NES 7-pin vs expansion-only) | TBD |
| Bypass caps, pull resistors | ~6 | Decoupling, safe defaults | ~20–50 |
| Removed: none of the Rev.A logic is removed; the GP22 PWM filter parts become unused | | | −(small) |
| **Approx. delta** | | | **~450–1,100 JPY** + controller connectors |

No second MCU, FPGA or display is added.

## Firmware pin-map validator check

`firmware/pio_bringup/CMakeLists.txt` validates only the six **test-loopback** pins (accepts GP0–GP22 and GP26–GP28; rejects duplicates, malformed/leading-zero values, out-of-range values and GP23/24/25/29). It is not a cartridge pin-map contract, so it does not apply to this map directly. Checked against the same rules by inspection: every Rev.B digital assignment is in GP0–GP22, there are no duplicates (23 distinct pins), and none of GP23–GP25/GP29 is used. A loopback configuration drawn from Rev.B pins (e.g. GP20–GP22) would therefore pass. The default loopback map (GP2–GP8) is unchanged. `validate_pio_source.py` still passes because no PIO/C source was changed. No CI files were modified. `hardware/kicad/validate_rev_a_logic.py` still checks the **Rev.A** map and has not been updated for Rev.B.

## Measured constraint: no internal pull-downs (RP2350 E9)

Bare-board measurement on a XIAO RP2350 (see [`docs/benchmark-results.md`](../../docs/benchmark-results.md)): with the internal pull-down enabled, a Hi-Z data pin kept its last driven value for >1 ms. The internal pull-up needed 220–433 ns, and with no pull the value was held ≥1 ms. **Rev.B therefore requires external pull resistors** on the CPU/PPU data lanes (or a defined bus-keeper policy), /IRQ, CIRAM status inputs, SR_QH and all OE/strobe default nets. No function may depend on an internal pull-down. Values (a few kΩ, sized for recovery vs drive load) are open. Preferred sys clock is now **172 MHz** (PLL-achievable; 171.8 MHz requested gives 172.0 MHz).

## Open questions

1. Accept 3-bit CVBS, or free a pin for 4-bit? Candidates: merge PPU_ALE+PPU_STB into one sequenced pin (adds PPU-path logic and latency on the tightest bus), or merge CPU_ALE into M2-derived sequencing.
2. Analog audio beside CVBS (1 PWM pin + RC): only possible by freeing a pin (as in 1), or with a cheap I2S/PWM-less approach. Is USB UAC-only audio acceptable for Rev.B?
3. Should pin 45 still be fed with the APU mix for authentic expansion-audio carts? That requires the PWM pin back.
4. 165/595 chain from control-latch bits (≈20 µs refresh) vs memory-mapped $4016/$4017 parallel buffers (cycle-exact, 0 GPIO, closer to real hardware): which does the user prefer?
5. Controllers: physical Famicom-style pads (hardwired in a real Famicom), NES 7-pin ports, expansion-port-only pads, or host-forwarded USB input only?
6. System clock: 150 / 157.5 / 171.8 MHz?
7. Does /IRQ latency through the status MUX (possibly HBlank-only during rendering) meet MMC3-class timing? This needs simulation with the real fetch schedule.
8. Level interfacing of the 5 V 165/595 chain and expansion port (HCT at 5 V, QH via LVC257A) and ESD on the external DA-15.
9. UVC bonus mode: worth the descriptor/firmware complexity on Full Speed?
10. If any of the above fails measurement, revisit the RP2350B (48 GPIO) board per the roadmap's stop/pivot rule.

## Freeze gates before a full PCB layout (unchanged in substance)

1. Implement the Rev.B CPU 3-phase and PPU sequences in PIO; capture logic-analyzer traces with simultaneous CPU/PPU activity and the CVBS SM running.
2. Update the Rev.A logic/Boolean validators (or add Rev.B ones) for the latched R/W, RD/WR selects and SR control bits.
3. Verify connector, part numbers, levels, power-off isolation and ESD as in Rev.A gates.
4. Measure CVBS levels on a real 75 Ω load/TV and USB throughput on real hosts.
5. No PCB order or fabrication release is implied by this document.

Rev.A references retained: bring-up fixture pin-number check and J5 ADC ordering are documented in [`bringup/README.md`](bringup/README.md); the Rev.A candidate partition remains in [`rev-a-circuit-spec.md`](rev-a-circuit-spec.md).

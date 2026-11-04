# Host-side simulation results

The original deterministic Python scheduler baseline passed 21/21 tests; its initial GitHub Actions status had not been independently verified at that time. Current verification is recorded in the development log.

**These are model outcomes, not measured Raspberry Pi Pico 2 / PIO performance.** The model assumes transactions (including addresses and data) are ready and PIO/FIFO/DMA scheduling has no additional stalls.

## Baseline assumptions

- NTSC CPU: 1,789,773 Hz, PPU: 5,369,318 Hz.
- A simulated 262-scanline frame generates 29,781 approximate CPU-cycle slots and 40,970 PPU fetch slots: 170 per rendering scanline on visible lines 0–239 and pre-render line 261.
- Each transaction consumes 12 clocks at 150 MHz plus 22 ns of propagation/settling = 102 ns.
- CPU deadline: 320 ns; PPU deadline: 180 ns (both *assumed*).
- Either separate CPU and PPU engines, or one serialized engine shared by both.
- PPU slot phases are classified from [NESdev's PPU rendering timing](https://www.nesdev.org/wiki/PPU_rendering); the addresses, render-enable state, actual sprite contents, and CPU bus addresses are not generated. Treat this as a timing-slot model, not a complete bus trace.

## Results

| Clock | Transaction | Engines | Deadline misses/frame | Worst latency |
| --- | --- | --- | ---: | ---: |
| 150 MHz | 12 cycles + 22 ns | Independent CPU/PPU | 0 | 102 ns |
| 150 MHz | 12 cycles + 22 ns | Shared | 13,657 | 204 ns |
| 150 MHz | 10 cycles + 22 ns | Shared | 0 | 177.3 ns |
| 150 MHz | 24 cycles + 22 ns | Shared | 40,970 | 364 ns |
| 150 MHz | 48 cycles + 22 ns | Independent CPU/PPU | 70,751 | 342 ns |
| 150 MHz | 48 cycles + 22 ns | Shared | 70,751 | ~8.04 ms |

Under the modeled workload, CPU and PPU service windows **overlap 13,657 times** for the 12-cycle independent-engine run. One shared bus thus misses deadlines at the assumed 12-cycle latency. However, the 10-cycle shared configuration passes this simplified model; multiplexing is **not proven impossible**.

## What these results DO NOT establish

- Whether the RP2350 can calculate all CPU and PPU accesses accurately on time.
- Whether the 74-series latch + transceiver control can be implemented in 10–12 PIO clocks.
- Whether the on-board USB and software video encoding fit the CPU budget.
- Whether the standard Pico 2's 26 exposed header GPIOs, combined with external latches/transceivers, can support a workable Famicom 60-pin interface.
- Whether MMC3 A12/M2 timing, CIRAM, open bus, and cartridge removal work electrically.

## Next test

Build and compile a PIO transaction sequencer, count its instruction cycles and measure real output/input timings on Raspberry Pi Pico 2 with loopback before designing the cartridge PCB. Replace nominal workloads with recorded/verified 6502/PPU bus traces.

## Follow-up: request preparation cost

Added `nespico/pipeline.py` and `tests/test_pipeline.py`. This is a deliberately **conservative model with no lookahead**: the CPU/PPU must prepare an address before its PIO bus transaction. It still assumes zero DMA/FIFO setup overhead.

At 150 MHz, with the same **assumed** 12 bus clocks + 22 ns settling, 320 ns CPU and 180 ns PPU deadlines:

| CPU preparation | PPU preparation | CPU misses/frame | PPU misses/frame |
|---:|---:|---:|---:|
| 0 cycles | 0 cycles | 0 | 0 |
| 10 cycles | 10 cycles | 0 | 0 |
| 30 cycles | 10 cycles | 0 | 0 |
| 40 cycles | 10 cycles | 29,781 | 0 |
| 10 cycles | 12 cycles | 0 | 40,970 |
| 10 cycles | 16 cycles | 0 | 40,970 |

One full NTSC-like simulated frame contains 29,781 CPU-cycle slots and 40,970 PPU fetch slots. **These numbers are NOT measured MCU performance and the events are not address-accurate.** Computation may be pipelined earlier, but real instruction emulation, PPU address generation, DMA FIFO delivery, USB interrupts and jitter may cost considerably more. This shows why merely getting zero deadline misses in the original bus-only timing model does not justify fabricating a PCB.

**Go/no-go:** Continue host software and Pico 2 PIO timing development. Do not freeze a GPIO map or order the two cartridge PCBs until (1) an actual PIO instruction sequence exists, (2) per-access producer budgets are measured or bounded on RP2350, (3) the 27-signal concept is reconciled with Pico 2's 26 exposed header GPIOs, and (4) the CPU/PPU bus and 5 V electrical interface are reviewed.

## Rev.B GPIO-allocation phase budget (screening, 2026-10-12)

`nespico/revb.py` + `tests/test_revb.py` add a per-cycle **phase budget** for the Rev.B proposal in [`hardware/kicad/board-plan.md`](../hardware/kicad/board-plan.md). Every input is an **assumption**: PIO instruction counts (3 clocks per latch load, 2 for turnaround, 3 for sync+sample, 2+3 for a status-MUX read) and part delays (AHCT574 10 ns, AHCT244/gates 8 ns, LVC 6–7 ns, PRG ROM 200 ns, CHR ROM 150 ns). It is not a PIO program, a gate-level model or a measurement, and it does not include emulator producer time (see the pipeline section above, which is still the bigger risk). The existing event simulator is unchanged.

- CPU: 3 loads (addr lo, addr hi, control) must finish inside M2 low (3/8 × 558.7 ns ≈ 209.5 ns); ROM access + RX + sample must fit in M2 high (≈ 349.2 ns).
- PPU: 2 loads + strobe + CHR access + sample + turnaround (+ status read) in one 2-dot slot (≈ 372.5 ns).

| Case | sys MHz | CPU M2-low margin | CPU M2-high margin | PPU slot margin | Status every slot | Worst /IRQ visibility |
|---|---:|---:|---:|---:|---|---:|
| nominal | 150 | 118 ns | 115 ns | 65 ns | yes | ~0.37 µs |
| nominal | 157.5 | 122 ns | 116 ns | 71 ns | yes | ~0.37 µs |
| nominal | 171.8 | 128 ns | 118 ns | 81 ns | yes | ~0.37 µs |
| CHR ROM 200 ns | 150 | 118 | 115 | 15 | yes | ~0.37 µs |
| CHR ROM 250 ns | 150 / 171.8 | 118 / 128 | 115 / 118 | 5 / 17 (status dropped) | **no** | ~63.5 µs (1 line) |
| PRG ROM 250 ns | 150 | 118 | 65 | 65 | yes | ~0.37 µs |
| PIO counts doubled | 150 / 171.8 | 45 / 64 | 109 / 112 | 32 (no status) / 11 | 150: **no**, 171.8: yes | 63.5 / 0.37 µs |

At 150 MHz the per-slot status read stops fitting once CHR access is ≥ ~215 ns. Then /IRQ (and CIRAM/SR_QH) can only be sampled outside rendering fetches, and MMC3 IRQ visibility degrades to about one scanline. That is functionally tolerable for many games but not for raster-split timing-sensitive titles. **The $4016/$4017 parallel-buffer alternative does not change these numbers**: R/W still needs the third (control) latch, and a local buffer read is an ordinary CPU cycle that is faster than ROM. It only frees the SR bits and the SR_QH MUX channel.

**Screening verdict:** Rev.B bus phases pass under nominal assumptions at all three clocks, with the PPU slot as the tightest (65–81 ns). This is not proof. Before schematic work: write the actual PIO for the CPU 3-load and PPU sequences, measure them on a Pico 2 with real latches, measure real cartridge ROM access times, and bound emulator producer time. If slow CHR ROMs are common, add a dedicated /IRQ input (needs a freed GPIO) or move status sampling out of the PPU slot.

### Rev.B update: measured PIO clock counts (XIAO RP2350 bare board, 2026-10-13)

`firmware/pio_timing_xiao` v1 was run on a Seeed XIAO RP2350 (Pico SDK 2.2.0) with **no external latches, ROM or wiring**. It ran 20,000 iterations × 16 blocks, DMA-fed, with no RX stall. The CPU sequence took **18.00 PIO clocks** (incl. pull/push and the post-read Hi-Z step) and the PPU sequence took **21.00**, at 150 MHz, 157.5 MHz and 172.0 MHz (171.8 was requested; the PLL gave 172.0). These counts match the static instruction count. The v1 source comment said 22 for the PPU sequence; that was a miscount. This is a **PIO-only** measurement: part delays and ROM access are still the assumed values above. `nespico/revb.py` now defaults to a `measured` profile (CPU: 12 clocks in M2-low, 6 in M2-high; PPU: 21 including the status read). The earlier assumptions remain as the `assumed` profile.

| Case (measured profile) | 150 MHz | 157.5 MHz | 172.0 MHz |
|---|---|---|---|
| Nominal (PRG 200, CHR 150 ns): CPU low / high / PPU | 112 / 95 / 52 ns | 115 / 97 / 58 | 122 / 100 / 69 |
| CHR 200 ns: PPU | 1.5 ns (status still fits) | 8 | 19 |
| CHR 250 ns: PPU | **−8 FAIL** (no status) | **−3 FAIL** | 5.5 (status dropped → /IRQ ~1 line) |
| PRG 250 ns: CPU high | 45 | 47 | 50 |
| PRG 300 ns: CPU high | **−5 FAIL** | **−3 FAIL** | 0.3 |

**Readback anomaly:** v1 read back the last driven byte (CPU `0xA5`, PPU `0x5A5A`) after the lane was set to Hi-Z, instead of `0x00` from the pull-downs. Hypotheses:

- The IN runs only 3–6 clocks (≈ 20–40 ns) after Hi-Z, while a ~50 kΩ internal pull-down on a few pF decays over ~0.1–1 µs.
- RP2350 erratum **E9** (Bank 0 pad leakage/latching when the input buffer is enabled with a pull-down) can hold a floating pin near ~2 V indefinitely.

v2 sweeps this delay. On a real bus this means the lane behaves like a bus keeper. A stale value can be misread as cartridge data (and as open-bus behaviour), and status/IRQ lines must not rely on internal pulls. Use external pull resistors (a few kΩ) where a defined idle level matters, and only sample after the cartridge buffer is known to be driving.

### Rev.B update: Hi-Z decay sweep (XIAO RP2350 v2, 150 MHz, bare board)

| Pull | Result |
|---|---|
| down (`pde_mask=0xff`, enabled) | **never decays**: the driven pattern is still read after 1 ms → RP2350 erratum **E9** behaviour confirmed on this board |
| up | reaches 0xFF between **220 and 433 ns** after Hi-Z |
| none | holds the last value ≥ 1 ms (one bit flipped at 1 ms) |

Consequences: the design **must not rely on the internal pull-down**. Every lane or status line whose idle level matters needs an **external pull resistor** (value TBD, a few kΩ for sub-100 ns recovery). The internal pull-up (~220–433 ns) is too slow to define a level within one PPU slot. **172 MHz** is now the preferred sys clock.

### Rev.B update: optimized PIO candidates (v3, proposal — not yet measured)

`firmware/pio_timing_xiao` v3 measures the old and optimized programs side by side (at 150/157.5/172 MHz).

- CPU **18 → 11** clocks: autopull/autopush, 1-clock side-set ALE high, Hi-Z merged with the last ALE-low edge, `.wrap`.
- PPU **21 → 13** clocks: likewise, plus the STB assert merged with Hi-Z.

Caveat: a 1-clock ALE high is ~5.8 ns at 172 MHz, which is at or below typical 74AHCT574 minimum clock pulse width, so a `[1]` delay may be needed (+1 clock per load). `revb.py` profile `proposed` (pending measurement):

| Case (proposed profile) | 150 MHz | 172 MHz |
|---|---|---|
| Nominal: CPU low / high / PPU | 145 / 109 / 105 ns | 151 / 112 / 116 |
| CHR 250 ns: PPU | 4.8 (status fits) | 15.9 |
| PRG 300 ns: CPU high | 8.5 | 12.0 |

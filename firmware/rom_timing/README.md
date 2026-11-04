# Cartridge ROM access-time measurement — skeleton (DO NOT RUN YET)

**Status: build-only skeleton.** It has never been run, and no latch/transceiver board exists yet. Running it requires the Rev.B interface (5 V-side AHCT latches/buffers, LVC receive path, **external pull resistors** — the RP2350 internal pull-down is unusable per erratum E9, measured on XIAO RP2350). **Never connect any RP2350 pin directly to a cartridge.**

## Method

For a fixed CPU (PRG) or PPU (CHR) address, the PIO loads the address latches (Rev.B CPU sequence), asserts M2 (or PPU_STB), and waits `d` PIO clocks before sampling the data lane. The firmware sweeps `d` upward and, for each `d`, reads `REPEATS` times. Estimated access time ≈ the smallest `d` at which all repeats equal the reference value (taken at the largest `d`) × clock period, **minus** the interface delays (latch, buffers, input sync). Those delays must be measured separately on the board, e.g. with a logic analyzer. Data before the ROM drives is stale lane charge (bus-keeper behaviour), which is exactly why external pulls are needed: pull the lane opposite to the expected data so that "not yet valid" is detectable.

## Pinout (Rev.B proposal, Pico 2 numbering — not a frozen map)

| GPIO | Signal |
|---|---|
| GP0–GP7 | CPU data lane (also latch loads) |
| GP8–GP15 | PPU data lane |
| GP16 | CPU M2 |
| GP17 | CPU_ALE |
| GP18 | PPU_ALE |
| GP19 | PPU_STB |

GP20–22 (CVBS) and GP26–28 (ADC) are not touched.

## Safety interlocks in the code

- The bus code is compiled only with `-DNESPICO_ROM_TIMING_ARMED=1` (default 0 → the firmware only prints a refusal line).
- Even when armed, it waits for the user to type `ARM` over USB serial.
- **Read cycles only:** R/W is held high (read) in the control byte, and there are no writes, so no mapper registers are touched.

// ROM access-time probe skeleton. NOT validated; see README.md before use.
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "rom_read.pio.h"

#ifndef NESPICO_ROM_TIMING_ARMED
#define NESPICO_ROM_TIMING_ARMED 0
#endif
#define CPU_DATA_BASE 0u
#define CPU_SIDE_BASE 16u   // GP16 = M2 (side bit0), GP17 = CPU_ALE (bit1): rom_read_cpu
#define PPU_DATA_BASE 8u
#define PPU_SIDE_BASE 18u   // GP18 = PPU_ALE (bit0), GP19 = PPU_STB (bit1)
#define REPEATS 64u
#define MAX_DELAY 96u
#define CTRL_READ 0x01u     // control latch bit0 = R/W (1 = read)

static int probe(PIO pio, uint sm, uint off, bool cpu, uint data_base, uint side_base,
                 uint32_t addr, uint32_t *ref_out) {
    pio_sm_config c = cpu ? rom_read_cpu_program_get_default_config(off)
                          : rom_read_ppu_program_get_default_config(off);
    sm_config_set_out_pins(&c, data_base, 8);
    sm_config_set_in_pins(&c, data_base);
    sm_config_set_sideset_pins(&c, side_base);
    sm_config_set_out_shift(&c, true, false, 32);
    sm_config_set_in_shift(&c, false, false, 32);
    pio_sm_init(pio, sm, off, &c);
    pio_sm_set_consecutive_pindirs(pio, sm, side_base, 2, true);
    pio_sm_set_enabled(pio, sm, true);
    uint32_t word = (addr & 0xffffu) | ((uint32_t)CTRL_READ << 16);
    uint32_t ref;
    pio_sm_put_blocking(pio, sm, word); pio_sm_put_blocking(pio, sm, MAX_DELAY);
    ref = pio_sm_get_blocking(pio, sm) & 0xffu;
    *ref_out = ref;
    for (uint32_t d = 1; d <= MAX_DELAY; d++) {
        bool stable = true;
        for (uint r = 0; r < REPEATS && stable; r++) {
            pio_sm_put_blocking(pio, sm, word); pio_sm_put_blocking(pio, sm, d);
            stable = (pio_sm_get_blocking(pio, sm) & 0xffu) == ref;
        }
        if (stable) { pio_sm_set_enabled(pio, sm, false); return (int)d; }
    }
    pio_sm_set_enabled(pio, sm, false);
    return -1;
}

int main(void) {
    stdio_init_all();
    set_sys_clock_khz(172000, false);
    for (;;) {
        sleep_ms(3000);
        printf("NESPICO_ROM_TIMING skeleton armed=%d clk_hz=%lu\n", NESPICO_ROM_TIMING_ARMED,
               (unsigned long)clock_get_hz(clk_sys));
#if !NESPICO_ROM_TIMING_ARMED
        printf("REFUSED: built without NESPICO_ROM_TIMING_ARMED=1; no pins configured\nDONE\n");
#else
        printf("Type ARM + Enter to run read-only probes (interface board required)\n");
        char buf[8] = {0}; int n = 0;
        while (n < 7) { int ch = getchar_timeout_us(10000000); if (ch < 0 || ch == '\r' || ch == '\n') break; buf[n++] = (char)ch; }
        if (strcmp(buf, "ARM") != 0) { printf("NOT_ARMED\nDONE\n"); continue; }
        PIO pio = pio0;
        uint off_c = pio_add_program(pio, &rom_read_cpu_program);
        uint off_p = pio_add_program(pio, &rom_read_ppu_program);
        for (uint i = 0; i < 8; i++) { pio_gpio_init(pio, CPU_DATA_BASE + i); pio_gpio_init(pio, PPU_DATA_BASE + i); }
        for (uint i = 0; i < 2; i++) { pio_gpio_init(pio, CPU_SIDE_BASE + i); pio_gpio_init(pio, PPU_SIDE_BASE + i); }
        const uint32_t prg[] = {0x8000, 0xC000, 0xFFFC, 0xFFFD};
        const uint32_t chr[] = {0x0000, 0x0FF0, 0x1000, 0x1FF0};
        double ns = 1e9 / clock_get_hz(clk_sys);
        for (uint i = 0; i < 4; i++) {
            uint32_t ref; int d = probe(pio, 0, off_c, true, CPU_DATA_BASE, CPU_SIDE_BASE, prg[i], &ref);
            printf("PRG addr=0x%04lx ref=0x%02lx stable_delay_clk=%d raw_ns=%.1f\n", (unsigned long)prg[i], (unsigned long)ref, d, d * ns);
        }
        for (uint i = 0; i < 4; i++) {
            uint32_t ref; int d = probe(pio, 1, off_p, false, PPU_DATA_BASE, PPU_SIDE_BASE, chr[i], &ref);
            printf("CHR addr=0x%04lx ref=0x%02lx stable_delay_clk=%d raw_ns=%.1f\n", (unsigned long)chr[i], (unsigned long)ref, d, d * ns);
        }
        pio_remove_program(pio, &rom_read_cpu_program, off_c);
        pio_remove_program(pio, &rom_read_ppu_program, off_p);
        printf("NOTE raw_ns includes latch/buffer/sync delays; subtract measured interface delay\nDONE\n");
#endif
    }
}

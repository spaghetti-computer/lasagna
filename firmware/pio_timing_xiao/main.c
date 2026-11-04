// NESPICO Rev.B PIO timing measurement for Seeed XIAO RP2350.
// Test fixture only: no external wiring, no cartridge. Not a bus driver.
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "revb_seq.pio.h"

#define DATA_BASE 0u   // GP0..GP7 = XIAO D6,D7,D8,D10,D9,D3,D4,D5 (verify)
#define SIDE_BASE 26u  // GP26 = ALE (D0), GP27 = PPU_STB (D1)
#define ITERS 20000u
#define BLOCKS 16u

// Static PIO clocks per sequence; must match revb_seq.pio and nespico/revb.py.
#define CPU_STATIC_CLOCKS 18u  // pull1 + drive2 + 3x3 loads + hiz2 + sync2 + in1 + push1
#define PPU_STATIC_CLOCKS 21u  // pull1 + drive2 + 2x3 + 1 + 2 + 1 + 2 + 2 + 2 + 1 + push1 (v1 said 22: miscount; measured 21)
#define CPU_OPT_CLOCKS 11u
#define PPU_OPT_CLOCKS 13u
#define CPU_MODEL_CLOCKS 14u   // revb.py: turnaround2 + 3*load3 + sample3
#define PPU_MODEL_CLOCKS 19u   // revb.py: 2 + 2*3 + 1 + 3 + 2 + status(2+3)

static const uint32_t clocks_khz[3] = {150000, 157500, 172000};

static uint32_t choose_khz(uint32_t want) {
    uint vco, p1, p2;
    for (uint32_t d = 0; d < 2000; d++) {
        if (check_sys_clock_khz(want - d, &vco, &p1, &p2)) return want - d;
        if (check_sys_clock_khz(want + d, &vco, &p1, &p2)) return want + d;
    }
    return 150000;
}

static void pins_init(PIO pio) {
    for (uint i = 0; i < 8; i++) {
        pio_gpio_init(pio, DATA_BASE + i);
        gpio_set_drive_strength(DATA_BASE + i, GPIO_DRIVE_STRENGTH_2MA);
        gpio_pull_down(DATA_BASE + i);
    }
    for (uint i = 0; i < 2; i++) {
        pio_gpio_init(pio, SIDE_BASE + i);
        gpio_set_drive_strength(SIDE_BASE + i, GPIO_DRIVE_STRENGTH_2MA);
    }
}

typedef struct { double min_ns, avg_ns, max_ns, min_clk, avg_clk, max_clk; uint32_t last_in; bool stall; } result_t;

static result_t run(PIO pio, uint sm, uint offset, const pio_program_t *prog, bool ppu, bool opt) {
    pio_sm_config c = opt ? (ppu ? ppu_opt_program_get_default_config(offset)
                                 : cpu_opt_program_get_default_config(offset))
                          : (ppu ? ppu_seq_program_get_default_config(offset)
                                 : cpu_seq_program_get_default_config(offset));
    sm_config_set_out_pins(&c, DATA_BASE, 8);
    sm_config_set_in_pins(&c, DATA_BASE);
    sm_config_set_sideset_pins(&c, SIDE_BASE);
    if (opt) {
        sm_config_set_out_shift(&c, true, true, ppu ? 16 : 24);
        sm_config_set_in_shift(&c, false, true, ppu ? 16 : 8);
    } else {
        sm_config_set_out_shift(&c, true, false, 32);
        sm_config_set_in_shift(&c, false, false, 32);
    }
    sm_config_set_clkdiv(&c, 1.0f);
    pio_sm_set_consecutive_pindirs(pio, sm, SIDE_BASE, 2, true);
    pio_sm_set_consecutive_pindirs(pio, sm, DATA_BASE, 8, false);
    (void)prog;

    static uint32_t tx_word = 0x00A55A3Cu, rx_word;
    int tx = dma_claim_unused_channel(true), rx = dma_claim_unused_channel(true);
    double hz = (double)clock_get_hz(clk_sys);
    result_t r = {1e18, 0, 0, 0, 0, 0, 0, false};
    for (uint b = 0; b < BLOCKS; b++) {
        pio_sm_init(pio, sm, offset, &c);
        dma_channel_config tc = dma_channel_get_default_config(tx);
        channel_config_set_read_increment(&tc, false);
        channel_config_set_dreq(&tc, pio_get_dreq(pio, sm, true));
        dma_channel_configure(tx, &tc, &pio->txf[sm], &tx_word, ITERS, false);
        dma_channel_config rc = dma_channel_get_default_config(rx);
        channel_config_set_read_increment(&rc, false);
        channel_config_set_write_increment(&rc, false);
        channel_config_set_dreq(&rc, pio_get_dreq(pio, sm, false));
        dma_channel_configure(rx, &rc, &rx_word, &pio->rxf[sm], ITERS, true);
        pio->fdebug = 0xffffffffu;
        uint64_t t0 = time_us_64();
        dma_channel_start(tx);
        pio_sm_set_enabled(pio, sm, true);
        dma_channel_wait_for_finish_blocking(rx);
        uint64_t us = time_us_64() - t0;
        pio_sm_set_enabled(pio, sm, false);
        // TX stall is expected only at the very end; RX stall would be a DMA backlog.
        if (pio->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + sm))) r.stall = true;
        double ns = us * 1000.0 / ITERS;
        if (ns < r.min_ns) r.min_ns = ns;
        if (ns > r.max_ns) r.max_ns = ns;
        r.avg_ns += ns / BLOCKS;
    }
    r.min_clk = r.min_ns * hz / 1e9; r.max_clk = r.max_ns * hz / 1e9; r.avg_clk = r.avg_ns * hz / 1e9;
    r.last_in = rx_word;
    dma_channel_unclaim(tx); dma_channel_unclaim(rx);
    return r;
}

// ---- v2 Hi-Z decay sweep ----
static const uint32_t delays[] = {16, 32, 48, 64, 96, 128};  // v3: short, pull-up only
static const char *pull_names[] = {"down", "up", "none"};

static void set_pulls(int mode) {
    for (uint i = 0; i < 8; i++) {
        if (mode == 0) gpio_pull_down(DATA_BASE + i);
        else if (mode == 1) gpio_pull_up(DATA_BASE + i);
        else gpio_disable_pulls(DATA_BASE + i);
    }
}

static uint32_t sample_once(PIO pio, uint sm, uint off, bool zero, uint8_t pattern, uint32_t n) {
    pio_sm_config c = zero ? hiz_zero_program_get_default_config(off)
                           : hiz_decay_program_get_default_config(off);
    sm_config_set_out_pins(&c, DATA_BASE, 8);
    sm_config_set_in_pins(&c, DATA_BASE);
    sm_config_set_out_shift(&c, true, false, 32);
    sm_config_set_in_shift(&c, false, false, 32);
    sm_config_set_clkdiv(&c, 1.0f);
    pio_sm_init(pio, sm, off, &c);
    pio_sm_set_consecutive_pindirs(pio, sm, DATA_BASE, 8, false);
    pio_sm_set_enabled(pio, sm, true);
    pio_sm_put_blocking(pio, sm, pattern);
    if (!zero) pio_sm_put_blocking(pio, sm, n);
    uint32_t v = pio_sm_get_blocking(pio, sm) & 0xffu;
    pio_sm_set_enabled(pio, sm, false);
    sleep_us(200);  // let the pad settle before the next trial
    return v;
}

static void hiz_sweep(PIO pio, uint dec_off, uint zero_off) {
    uint32_t hz = clock_get_hz(clk_sys);
    for (int mode = 1; mode < 2; mode++) {  // v3: pull=up only (E9: pull-down unusable)
        set_pulls(mode);
        printf("HIZ_PADS pull=%s pde_mask=0x%02x pue_mask=0x%02x\n", pull_names[mode],
               (unsigned)({uint32_t d = 0; for (uint i = 0; i < 8; i++) d |= (uint32_t)gpio_is_pulled_down(DATA_BASE + i) << i; d;}),
               (unsigned)({uint32_t u = 0; for (uint i = 0; i < 8; i++) u |= (uint32_t)gpio_is_pulled_up(DATA_BASE + i) << i; u;}));
        const uint8_t patterns[1] = {0x00};
        for (int p = 0; p < 1; p++) {
            printf("HIZ pull=%s pattern=0x%02x delay_clk=1 delay_ns=%.1f read=0x%02lx\n", pull_names[mode],
                   patterns[p], 1e9 / hz, (unsigned long)sample_once(pio, 0, zero_off, true, patterns[p], 0));
            for (uint k = 0; k < sizeof delays / sizeof delays[0]; k++) {
                uint32_t n = delays[k];
                uint32_t v = sample_once(pio, 0, dec_off, false, patterns[p], n);
                printf("HIZ pull=%s pattern=0x%02x delay_clk=%lu delay_ns=%.1f read=0x%02lx\n", pull_names[mode],
                       patterns[p], (unsigned long)(n + 1), (n + 1) * 1e9 / hz, (unsigned long)v);
            }
        }
    }
    set_pulls(0);
}

int main(void) {
    stdio_init_all();
    PIO pio = pio0;
    uint cpu_off = pio_add_program(pio, &cpu_seq_program);
    uint ppu_off = pio_add_program(pio, &ppu_seq_program);
    uint cpu_opt_off = pio_add_program(pio2, &cpu_opt_program);
    uint ppu_opt_off = pio_add_program(pio2, &ppu_opt_program);
    uint dec_off = pio_add_program(pio1, &hiz_decay_program);
    uint zero_off = pio_add_program(pio1, &hiz_zero_program);
    pins_init(pio);
    uint32_t round = 0;
    while (true) {
        sleep_ms(3000);
        printf("NESPICO_PIO_TIMING v3 board=seeed_xiao_rp2350 round=%lu\n", (unsigned long)round++);
        printf("STATIC cpu_pio_clocks=%u ppu_pio_clocks=%u cpu_opt=%u ppu_opt=%u model_cpu=%u model_ppu=%u (static includes pull+push=2, cpu adds Hi-Z 2 not in model)\n",
               CPU_STATIC_CLOCKS, PPU_STATIC_CLOCKS, CPU_OPT_CLOCKS, PPU_OPT_CLOCKS, CPU_MODEL_CLOCKS, PPU_MODEL_CLOCKS);
        for (int i = 0; i < 3; i++) {
            uint32_t khz = choose_khz(clocks_khz[i]);
            bool ok = set_sys_clock_khz(khz, false);
            stdio_flush();
            uint32_t hz = clock_get_hz(clk_sys);
            result_t c = run(pio, 0, cpu_off, &cpu_seq_program, false, false);
            result_t p = run(pio, 1, ppu_off, &ppu_seq_program, true, false);
            for (uint i = 0; i < 8; i++) pio_gpio_init(pio2, DATA_BASE + i);
            for (uint i = 0; i < 2; i++) pio_gpio_init(pio2, SIDE_BASE + i);
            result_t co = run(pio2, 0, cpu_opt_off, &cpu_opt_program, false, true);
            result_t po = run(pio2, 1, ppu_opt_off, &ppu_opt_program, true, true);
            for (uint i = 0; i < 8; i++) pio_gpio_init(pio, DATA_BASE + i);
            for (uint i = 0; i < 2; i++) pio_gpio_init(pio, SIDE_BASE + i);
            printf("CLOCK req_khz=%lu set_khz=%lu ok=%d achieved_hz=%lu\n",
                   (unsigned long)clocks_khz[i], (unsigned long)khz, ok, (unsigned long)hz);
            printf("CPU iters=%u blocks=%u ns min=%.2f avg=%.2f max=%.2f clk min=%.2f avg=%.2f max=%.2f static=%u rxstall=%d last_in=0x%08lx\n",
                   ITERS, BLOCKS, c.min_ns, c.avg_ns, c.max_ns, c.min_clk, c.avg_clk, c.max_clk, CPU_STATIC_CLOCKS, c.stall, (unsigned long)c.last_in);
            printf("CPU_OPT iters=%u blocks=%u ns min=%.2f avg=%.2f max=%.2f clk min=%.2f avg=%.2f max=%.2f static=%u rxstall=%d last_in=0x%08lx\n",
                   ITERS, BLOCKS, co.min_ns, co.avg_ns, co.max_ns, co.min_clk, co.avg_clk, co.max_clk, CPU_OPT_CLOCKS, co.stall, (unsigned long)co.last_in);
            printf("PPU_OPT iters=%u blocks=%u ns min=%.2f avg=%.2f max=%.2f clk min=%.2f avg=%.2f max=%.2f static=%u rxstall=%d last_in=0x%08lx\n",
                   ITERS, BLOCKS, po.min_ns, po.avg_ns, po.max_ns, po.min_clk, po.avg_clk, po.max_clk, PPU_OPT_CLOCKS, po.stall, (unsigned long)po.last_in);
            printf("PPU iters=%u blocks=%u ns min=%.2f avg=%.2f max=%.2f clk min=%.2f avg=%.2f max=%.2f static=%u rxstall=%d last_in=0x%08lx\n",
                   ITERS, BLOCKS, p.min_ns, p.avg_ns, p.max_ns, p.min_clk, p.avg_clk, p.max_clk, PPU_STATIC_CLOCKS, p.stall, (unsigned long)p.last_in);
        }
        set_sys_clock_khz(150000, false);
        // Hi-Z sweep runs on PIO1 SM2 at 150 MHz; GPIO function moved to PIO1 for the sweep.
        for (uint i = 0; i < 8; i++) pio_gpio_init(pio1, DATA_BASE + i);
        printf("HIZ_SWEEP clk_hz=%lu note=delay_clk_counts_from_MOV_PINDIRS_to_IN\n", (unsigned long)clock_get_hz(clk_sys));
        hiz_sweep(pio1, dec_off, zero_off);
        for (uint i = 0; i < 8; i++) pio_gpio_init(pio, DATA_BASE + i);
        printf("DONE\n");
    }
}

// NESPICO latch/decoder/turnaround bench for Seeed XIAO RP2350 (no cartridge, no logic analyzer).
// The XIAO measures itself: PIO snapshots all GPIOs once per sys clock (1 clk = 5.81 ns @172 MHz).
// Wiring: see docs/nespico_breadboard_min.md.  GP0-3 = D0-3 out (XIAO D6,D7,D8,D10),
// GP4-7 = Q0-3 in (D9,D3,D4,D5), GP26 = ALE/LE/CLK (D0), GP27 = '138 /Y0 (D1), GP28 = '138 /Y3 (D2).
// Safe with nothing wired: outputs are 2 mA drive, inputs use internal pull-ups, every test
// reports NOT WIRED / NO RESPONSE instead of hanging, and the run always ends with "DONE".
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "bench.pio.h"

#define D_BASE 0u
#define Q_SHIFT 4u
#define ALE_PIN 26u
#define Y0_PIN 27u
#define Y3_PIN 28u
#define SYS_KHZ 172000u
#define NWIN 8u

static PIO cp = pio0, pp = pio1;
static uint csm = 0, psm = 0, coff, poff;

static void gpio_setup(void) {
    for (uint i = 0; i < 4; i++) {           // D0..D3: PIO-driven, no internal pull (E9: rely on external array)
        pio_gpio_init(cp, D_BASE + i); gpio_disable_pulls(D_BASE + i);
        gpio_set_drive_strength(D_BASE + i, GPIO_DRIVE_STRENGTH_2MA);
    }
    pio_gpio_init(cp, ALE_PIN); gpio_disable_pulls(ALE_PIN);
    gpio_set_drive_strength(ALE_PIN, GPIO_DRIVE_STRENGTH_2MA);
    for (uint i = 4; i < 8; i++) { gpio_init(i); gpio_set_dir(i, false); gpio_pull_up(i); }
    gpio_init(Y0_PIN); gpio_set_dir(Y0_PIN, false); gpio_pull_up(Y0_PIN);
    gpio_init(Y3_PIN); gpio_set_dir(Y3_PIN, false); gpio_pull_up(Y3_PIN);
}

static void cap_init(void) {
    coff = pio_add_program(cp, &cap_program);
    pio_sm_config c = cap_program_get_default_config(coff);
    sm_config_set_out_pins(&c, D_BASE, 4);
    sm_config_set_in_pins(&c, 0);
    sm_config_set_sideset_pins(&c, ALE_PIN);
    sm_config_set_out_shift(&c, true, false, 32);
    sm_config_set_in_shift(&c, false, true, 32);
    sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_RX);   // 8-deep RX: holds all 8 snapshots
    sm_config_set_clkdiv(&c, 1.0f);
    pio_sm_set_consecutive_pindirs(cp, csm, ALE_PIN, 1, true);
    pio_sm_set_pins_with_mask(cp, csm, 0, (1u << ALE_PIN) | 0xFu);
    pio_sm_set_consecutive_pindirs(cp, csm, D_BASE, 4, true);
    pio_sm_init(cp, csm, coff + cap_offset_hold, &c);
    pio_sm_set_enabled(cp, csm, true);
}

// Clock index (relative to event) of snapshot i given delay x.
enum { M_ALE, M_D, M_REL };
static uint cap_first(int mode, uint x) { return x + (mode == M_ALE ? 2 : 3); }

// One capture: returns false on timeout (never hangs).
static bool cap_run(int mode, uint dirs0, uint d0, uint x, uint d1, uint32_t s[NWIN]) {
    uint head = mode == M_ALE ? cap_offset_ale_head : mode == M_D ? cap_offset_d_head : cap_offset_rel_head;
    pio_sm_clear_fifos(cp, csm);
    pio_sm_exec(cp, csm, pio_encode_jmp(coff + head));
    pio_sm_put(cp, csm, (dirs0 & 0xF) | (d0 & 0xF) << 4 | (x & 0xFF) << 8 | (d1 & 0xF) << 16);
    for (uint i = 0; i < NWIN; i++) {
        absolute_time_t to = make_timeout_time_ms(5);
        while (pio_sm_is_rx_fifo_empty(cp, csm)) if (time_reached(to)) return false;
        s[i] = pio_sm_get(cp, csm);
    }
    return true;
}

// Build a trace of up to len clocks (index = clk after event) by sliding the 8-sample window.
static bool trace(int mode, uint dirs0, uint d0, uint d1, uint len, uint32_t *tr, uint8_t *valid) {
    memset(valid, 0, len);
    for (uint x = 0; cap_first(mode, x) < len; x += NWIN) {
        uint32_t s[NWIN];
        if (!cap_run(mode, dirs0, d0, x, d1, s)) return false;
        for (uint i = 0; i < NWIN; i++) { uint t = cap_first(mode, x) + i; if (t < len) { tr[t] = s[i]; valid[t] = 1; } }
    }
    return true;
}

static int first_match(const uint32_t *tr, const uint8_t *v, uint len, uint32_t mask, uint32_t want) {
    for (uint t = 0; t < len; t++) {
        if (!v[t] || (tr[t] & mask) != want) continue;
        bool stable = true;                       // must stay there until end of trace
        for (uint u = t; u < len; u++) if (v[u] && (tr[u] & mask) != want) { stable = false; break; }
        if (stable) return (int)t;
    }
    return -1;
}

static void pre(int mode, uint dirs0, uint d0, uint d1) { uint32_t s[NWIN]; cap_run(mode, dirs0, d0, 0, d1, s); }
#define TLEN 72u
static uint32_t tr[260]; static uint8_t tv[260];
static double ns_per_clk;

typedef struct { int min, max; uint32_t sum, n, fail; } stat_t;
static void st_add(stat_t *s, int v) { if (v < 0) { s->fail++; return; } if (!s->n || v < s->min) s->min = v; if (!s->n || v > s->max) s->max = v; s->sum += v; s->n++; }
static void st_print(const char *name, stat_t *s, int off) {
    if (!s->n) { printf("%-28s NO RESPONSE (fail=%lu)\n", name, (unsigned long)s->fail); return; }
    double avg = (double)s->sum / s->n - off;
    printf("%-28s min=%d avg=%.2f max=%d clk  (%.1f/%.1f/%.1f ns) n=%lu fail=%lu\n", name,
           s->min - off, avg, s->max - off, (s->min - off) * ns_per_clk, avg * ns_per_clk,
           (s->max - off) * ns_per_clk, (unsigned long)s->n, (unsigned long)s->fail);
}

// ---------- Tests ----------
static int L = -1;   // pad-out -> PIO-in loop latency (clk), measured on D readback

static void t_calib(void) {
    stat_t s = {0};
    for (uint r = 0; r < 64; r++) for (uint p = 0; p < 16; p++) {
        uint a = p, b = p ^ 0xF;
        if (!trace(M_D, 0xF, a, b, 24, tr, tv)) { s.fail++; continue; }
        st_add(&s, first_match(tr, tv, 24, 0xF, b));
    }
    printf("# T0 loopback latency (D pin out -> same pin in, includes 2-FF input sync)\n");
    st_print("T0 D readback", &s, 0);
    L = s.n ? s.min : 3;
    if (s.n && s.min != s.max) printf("WARN: readback latency not constant\n");
    printf("L=%d clk (subtracted from all following delays)\n", L);
}

static bool latch_present = false, transparent = false;

static void t_presence(void) {
    uint ok = 0, tok = 0;
    for (uint p = 0; p < 16; p++) {
        pre(M_ALE, 0xF, p ^ 0xF, 0); // precondition Q=~p
        if (trace(M_ALE, 0xF, p, 0, TLEN, tr, tv) && ((tr[TLEN - 1] >> Q_SHIFT) & 0xF) == p) ok++;
        if (trace(M_D, 0xF, p ^ 0xF, p, TLEN, tr, tv) && ((tr[TLEN - 1] >> Q_SHIFT) & 0xF) == p) tok++;
    }
    latch_present = ok == 16; transparent = tok == 16;
    printf("# T1 presence: ALE-edge capture %u/16, transparent follow %u/16 -> %s\n", ok, tok,
           !latch_present ? "LATCH NOT WIRED (Q pins read pull-ups) - skipping latch tests" :
           transparent ? "transparent latch (573-type)" : "edge-triggered (574-type)");
}

static void t_prop(void) {
    if (!latch_present) return;
    stat_t sa = {0}, sd = {0};
    for (uint r = 0; r < 32; r++) for (uint p = 0; p < 16; p++) {
        uint q = p ^ 0xF;
        // ALE rising -> Q (D already stable at p, Q preconditioned to ~p)
        pre(M_ALE, 0xF, q, 0); // Q=~p; ALE head then sets D=p >=16 clk before its edge
        if (trace(M_ALE, 0xF, p, 0, TLEN, tr, tv)) st_add(&sa, first_match(tr, tv, TLEN, 0xFu << Q_SHIFT, p << Q_SHIFT));
        if (transparent) pre(M_ALE, 0xF, q, 0);
        if (transparent && trace(M_D, 0xF, q, p, TLEN, tr, tv))
            st_add(&sd, first_match(tr, tv, TLEN, 0xFu << Q_SHIFT, p << Q_SHIFT));
    }
    printf("# T2 propagation (all 4 bits settled, minus L)\n");
    st_print("T2a ALE/CLK rise -> Q", &sa, L);
    if (transparent) st_print("T2b D -> Q (LE high)", &sd, L);
}

static void pulse_init(void) {
    poff = pio_add_program(pp, &pulse_program);
    pio_sm_config c = pulse_program_get_default_config(poff);
    sm_config_set_out_pins(&c, D_BASE, 4);
    sm_config_set_in_pins(&c, 0);
    sm_config_set_sideset_pins(&c, ALE_PIN);
    sm_config_set_out_shift(&c, true, false, 32);
    sm_config_set_in_shift(&c, false, true, 32);
    sm_config_set_clkdiv(&c, 1.0f);
    pio_sm_init(pp, psm, poff, &c);
}

// Hand D0-3 + ALE pins between PIO0 (cap) and PIO1 (pulse).
static void pins_to(PIO p, uint sm) {
    for (uint i = 0; i < 4; i++) gpio_set_function(D_BASE + i, p == pio0 ? GPIO_FUNC_PIO0 : GPIO_FUNC_PIO1);
    gpio_set_function(ALE_PIN, p == pio0 ? GPIO_FUNC_PIO0 : GPIO_FUNC_PIO1);
    pio_sm_set_pins_with_mask(p, sm, 0, (1u << ALE_PIN) | 0xFu);
    pio_sm_set_pindirs_with_mask(p, sm, (1u << ALE_PIN) | 0xFu, (1u << ALE_PIN) | 0xFu);
}

static bool pulse_run(uint p, uint w, uint h, uint p2, uint *q) {
    pio_sm_put(pp, psm, (p & 0xF) | ((w - 1) & 0xFF) << 4 | (h & 0xFF) << 12 | (p2 & 0xF) << 20);
    absolute_time_t to = make_timeout_time_ms(5);
    while (pio_sm_is_rx_fifo_empty(pp, psm)) if (time_reached(to)) return false;
    *q = (pio_sm_get(pp, psm) >> Q_SHIFT) & 0xF;
    return true;
}

static void t_pulse(void) {
    if (!latch_present) return;
    pio_sm_set_enabled(cp, csm, false);
    pins_to(pp, psm);
    pio_sm_clear_fifos(pp, psm); pio_sm_restart(pp, psm);
    pio_sm_exec(pp, psm, pio_encode_jmp(poff));
    pio_sm_set_enabled(pp, psm, true);
    printf("# T3 ALE pulse width sweep: D=p set >=5 clk before ALE rise, ALE high w clk,\n"
           "#    D held for (h+1) clk after ALE fall then -> ~p; pass = Q==p. 200 x 16 patterns each\n");
    printf("w\\hold ");
    for (uint h = 0; h < 4; h++) printf("  %u clk     ", h + 1);
    printf("\n");
    int wmin[4] = {-1, -1, -1, -1};
    for (uint w = 1; w <= 12; w++) {
        printf("w=%2u (%5.1fns)", w, w * ns_per_clk);
        for (uint h = 0; h < 4; h++) {
            uint fail = 0, tot = 0, q;
            for (uint r = 0; r < 200; r++) for (uint p = 0; p < 16; p++) {
                uint n = p ^ 0xF;
                if (!pulse_run(n, 16, 4, n, &q)) { fail++; tot++; continue; }   // precondition Q=~p
                if (!pulse_run(p, w, h, n, &q)) { fail++; tot++; continue; }
                tot++; if (q != p) fail++;
            }
            printf(" %5lu/%-5lu", (unsigned long)fail, (unsigned long)tot);
            if (!fail && wmin[h] < 0) wmin[h] = w;
        }
        printf("\n");
    }
    for (uint h = 0; h < 4; h++) printf("min error-free ALE width @hold %u clk: %d clk\n", h + 1, wmin[h]);
    pio_sm_set_enabled(pp, psm, false);
    pins_to(cp, csm);
    pio_sm_exec(cp, csm, pio_encode_jmp(coff + cap_offset_hold));
    pio_sm_set_enabled(cp, csm, true);
}

static void t_decoder(void) {
    // 138: A,B,C = D0..D2, /Y0 -> GP27, /Y3 -> GP28. Look for spurious low pulses.
    uint ok = 0;
    for (uint c = 0; c < 8; c++) {
        if (!trace(M_D, 0xF, c ^ 7, c, 40, tr, tv)) continue;
        bool y0 = (tr[39] >> Y0_PIN) & 1, y3 = (tr[39] >> Y3_PIN) & 1;
        if (y0 == (c != 0) && y3 == (c != 3)) ok++;
    }
    printf("# T4 decoder: static check %u/8 -> %s\n", ok, ok == 8 ? "138 wired" : "138 NOT WIRED / wrong, skipping");
    if (ok != 8) return;
    stat_t sy0 = {0};
    uint glitches = 0, runs = 0;
    for (uint r = 0; r < 100; r++) for (uint a = 0; a < 8; a++) for (uint b = 0; b < 8; b++) {
        if (a == b) continue;
        if (!trace(M_D, 0xF, a, b, 40, tr, tv)) continue;
        runs++;
        for (uint t = 0; t < 40; t++) if (tv[t]) {
            if (a != 0 && b != 0 && !((tr[t] >> Y0_PIN) & 1)) { glitches++; printf("glitch /Y0 %u->%u at %d clk\n", a, b, (int)t - L); break; }
            if (a != 3 && b != 3 && !((tr[t] >> Y3_PIN) & 1)) { glitches++; printf("glitch /Y3 %u->%u at %d clk\n", a, b, (int)t - L); break; }
        }
        if (b == 0) st_add(&sy0, first_match(tr, tv, 40, 1u << Y0_PIN, 0));
    }
    printf("glitches seen: %u in %u transitions (only pulses >=~1 clk are reliably seen)\n", glitches, runs);
    st_print("T4 A/B/C -> /Y0 fall", &sy0, L);
}

static void t_turnaround(void) {
    // Drive D0-3 to v, release (Hi-Z), time until all 4 lines read !v. External 10k array decides.
    printf("# T5 bus turnaround after release (external pull array on D0-3; internal pulls OFF)\n");
    const uint LEN = 258;
    for (int v = 1; v >= 0; v--) {
        stat_t s = {0};
        uint want = v ? 0 : 0xF;
        for (uint r = 0; r < 20; r++) {
            if (!trace(M_REL, 0xF, v ? 0xF : 0, 0x0, LEN, tr, tv)) { s.fail++; continue; }
            st_add(&s, first_match(tr, tv, LEN, 0xF, want));
        }
        st_print(v ? "T5 drive 1 -> release -> 0" : "T5 drive 0 -> release -> 1", &s, L);
    }
    printf("(NO RESPONSE in one direction is expected: pull array pulls one way only. Both NO RESPONSE = no pull / not wired; bus holds >%.0f ns)\n", 255 * ns_per_clk);
    pre(M_ALE, 0xF, 0, 0);   // leave D driven low, ALE low
}

int main(void) {
    set_sys_clock_khz(SYS_KHZ, true);
    stdio_init_all();
    gpio_setup();
    cap_init();
    pulse_init();
    ns_per_clk = 1e9 / (double)clock_get_hz(clk_sys);
    absolute_time_t to = make_timeout_time_ms(15000);
    while (!stdio_usb_connected() && !time_reached(to)) sleep_ms(50);
    sleep_ms(500);
    for (;;) {
        printf("\nNESPICO latch_bench_xiao  sys=%lu Hz (%.2f ns/clk)\n", (unsigned long)clock_get_hz(clk_sys), ns_per_clk);
        t_calib();
        t_presence();
        t_prop();
        t_pulse();
        t_decoder();
        t_turnaround();
        printf("DONE\n");
        printf("(press 'r' to rerun)\n");
        while (getchar_timeout_us(1000000) != 'r') tight_loop_contents();
    }
}

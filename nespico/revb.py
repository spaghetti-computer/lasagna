"""Rev.B per-cycle phase budget screen. ASSUMED instruction counts and part
delays; NOT a PIO program, gate-level simulation or hardware measurement.

Rev.B (hardware/kicad/board-plan.md): CPU cycle = 3 latch loads over the CPU
data lane (addr lo, addr hi, control) in M2-low, then the M2-high access.
PPU 2-dot slot = 2 address loads + gated strobe + CHR read + optional status
(/IRQ, CIRAM, SR_QH) read through the LVC257A MUX, all inside one slot.
"""
from dataclasses import dataclass, replace

from nespico.sim import CPU_HZ, PPU_HZ

CPU_PERIOD_NS = 1e9 / CPU_HZ            # ~558.7 ns
PPU_SLOT_NS = 2e9 / PPU_HZ              # ~372.5 ns
M2_HIGH_FRACTION = 5 / 8                # NESdev: M2 high ~5/8 of the cycle (2A03)


@dataclass(frozen=True)
class RevBConfig:
    sys_mhz: float = 150.0
    # PIO instruction clocks (assumed, side-set used for strobes)
    load_clocks: int = 3        # out pins,8 ; ALE high ; ALE low/settle
    turnaround_clocks: int = 2  # both transceivers Hi-Z before lane reuse
    sample_clocks: int = 3      # 2-flop input sync + in pins,8
    strobe_setup_clocks: int = 1
    status_clocks: int = 2      # select MUX + settle (plus sample_clocks)
    cpu_loads: int = 3
    ppu_loads: int = 2
    # Part delays (assumed, typical-to-worst 74AHCT/LVC at 5 V / 3.3 V)
    latch_tpd_ns: float = 10.0  # 74AHCT574 clock->Q
    buffer_tpd_ns: float = 8.0  # AHCT244 / control gates
    rx_tpd_ns: float = 6.0      # LVC244A + LVC257A
    mux_tpd_ns: float = 7.0
    cpu_rom_access_ns: float = 200.0  # PRG ROM tACC from /ROMSEL (assumed)
    chr_rom_access_ns: float = 150.0  # CHR ROM tACC from address/RD (assumed)
    status_read: bool = True
    parallel_4016: bool = False  # $4016/7 via local 541/574: no SR bits
    # Measured profile overrides (None = compose from the per-step assumptions).
    # XIAO RP2350 bare-board PIO measurement, firmware/pio_timing_xiao v1:
    # CPU 18 clk = pull1 + drive2 + 3x3 loads [M2-low part: 12] + HiZ2 + sync2
    # + in1 + push1 [M2-high part: 6]; PPU 21 clk incl. status read + pull/push.
    cpu_low_total_clocks: int | None = None
    cpu_high_total_clocks: int | None = None
    ppu_total_clocks: int | None = None

    @property
    def clk_ns(self) -> float:
        return 1000.0 / self.sys_mhz


@dataclass(frozen=True)
class RevBResult:
    cpu_m2_low_margin_ns: float
    cpu_m2_high_margin_ns: float
    ppu_slot_margin_ns: float
    status_in_every_slot: bool
    irq_latency_worst_ns: float

    @property
    def passed(self) -> bool:
        return min(self.cpu_m2_low_margin_ns, self.cpu_m2_high_margin_ns,
                   self.ppu_slot_margin_ns) >= 0


def evaluate(cfg: RevBConfig) -> RevBResult:
    c = cfg.clk_ns
    m2_low = CPU_PERIOD_NS * (1 - M2_HIGH_FRACTION)
    m2_high = CPU_PERIOD_NS * M2_HIGH_FRACTION
    # Parallel $4016/7 decode does not remove the control latch (R/W is the 17th bit).
    loads = cfg.cpu_loads
    low_clk = cfg.cpu_low_total_clocks if cfg.cpu_low_total_clocks is not None \
        else cfg.turnaround_clocks + loads * cfg.load_clocks
    high_clk = cfg.cpu_high_total_clocks if cfg.cpu_high_total_clocks is not None \
        else cfg.sample_clocks
    cpu_low_need = low_clk * c \
        + cfg.latch_tpd_ns + cfg.buffer_tpd_ns
    cpu_high_need = cfg.buffer_tpd_ns + cfg.cpu_rom_access_ns + cfg.rx_tpd_ns \
        + high_clk * c
    ppu_core = (cfg.turnaround_clocks + cfg.ppu_loads * cfg.load_clocks
                + cfg.strobe_setup_clocks + cfg.sample_clocks
                + cfg.turnaround_clocks) * c \
        + cfg.latch_tpd_ns + cfg.buffer_tpd_ns + cfg.chr_rom_access_ns + cfg.rx_tpd_ns
    status = (cfg.status_clocks + cfg.sample_clocks) * c + cfg.mux_tpd_ns
    if cfg.ppu_total_clocks is not None:  # measured total already includes status
        status_clk = cfg.status_clocks + cfg.sample_clocks
        ppu_core = (cfg.ppu_total_clocks - status_clk) * c \
            + cfg.latch_tpd_ns + cfg.buffer_tpd_ns + cfg.chr_rom_access_ns + cfg.rx_tpd_ns
    ppu_margin_with_status = PPU_SLOT_NS - ppu_core - status
    every_slot = cfg.status_read and ppu_margin_with_status >= 0
    ppu_margin = ppu_margin_with_status if cfg.status_read and every_slot else PPU_SLOT_NS - ppu_core
    # If status does not fit per slot, it is read only in non-fetch time
    # (dots 341-ish / vblank): worst case about one scanline of rendering.
    irq = PPU_SLOT_NS if every_slot else 341 / PPU_HZ * 1e9
    return RevBResult(m2_low - cpu_low_need, m2_high - cpu_high_need,
                      ppu_margin, every_slot, irq)


PROFILES = {
    "assumed": {},
    "measured": {"cpu_low_total_clocks": 12, "cpu_high_total_clocks": 6,
                 "ppu_total_clocks": 21},
    # v3 optimized PIO (autopull/autopush, 1-clock ALE high, merged Hi-Z):
    # CPU 11 = drive1 + 3x2 loads [low 7] + HiZ1 + sync2 + in1 [high 4];
    # PPU 13 incl. status. PROPOSED, pending XIAO v3 measurement and latch tw check.
    "proposed": {"cpu_low_total_clocks": 7, "cpu_high_total_clocks": 4,
                 "ppu_total_clocks": 13},
}
CLOCKS = (150.0, 157.5, 171.8, 172.0)


def profile(name: str = "measured", **overrides) -> RevBConfig:
    return RevBConfig(**{**PROFILES[name], **overrides})


def sweep(clocks=CLOCKS, profile_name: str = "measured", **overrides) -> dict[float, RevBResult]:
    return {mhz: evaluate(replace(profile(profile_name, **overrides), sys_mhz=mhz))
            for mhz in clocks}

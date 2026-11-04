"""Rev.C (RP2354B, 48 GPIO) per-cycle phase budget screen.

PROPOSAL / ASSUMED. The clock counts are derived from the measured Rev.B PIO
behaviour (XIAO RP2350, firmware/pio_timing_xiao v1/v2). They are NOT
measurements of Rev.C. Topology "mux": CPU A0-7/D0-7 and PPU A0-7/D0-7 are
time-multiplexed on 8 GPIOs each, with one 74LVC573A address latch per bus
(as in a real NES PPU). All other address and control lines are driven
directly by GPIO. There is no level shifter and no status MUX: /IRQ and the
CIRAM pins are sampled directly together with the data.
"""
from dataclasses import dataclass, replace

from nespico.sim import CPU_HZ, PPU_HZ

CPU_PERIOD_NS = 1e9 / CPU_HZ
PPU_SLOT_NS = 2e9 / PPU_HZ
M2_HIGH_FRACTION = 5 / 8


@dataclass(frozen=True)
class RevCConfig:
    sys_mhz: float = 150.0
    # M2-low: pull + drive (out pins/pindirs) + ALE high + ALE low, then Hi-Z
    cpu_low_clocks: int = 6     # measured-style: pull1 + drive2 + 1 load x3
    cpu_high_clocks: int = 6    # measured-style: HiZ2 + sync2 + in1 + push1
    ppu_clocks: int = 15        # pull1+drive2+load3+HiZ2+RD1+sync2+in1+push1+turn2
    latch_tpd_ns: float = 8.0   # 74LVC573A LE->Q / D->Q at 3.3 V (assumed worst)
    pad_tpd_ns: float = 3.0     # RP2350 pad out/in (assumed)
    cpu_rom_access_ns: float = 200.0
    chr_rom_access_ns: float = 150.0

    @property
    def clk_ns(self) -> float:
        return 1000.0 / self.sys_mhz


@dataclass(frozen=True)
class RevCResult:
    cpu_m2_low_margin_ns: float
    cpu_m2_high_margin_ns: float
    ppu_slot_margin_ns: float

    @property
    def passed(self) -> bool:
        return min(self.cpu_m2_low_margin_ns, self.cpu_m2_high_margin_ns,
                   self.ppu_slot_margin_ns) >= 0


def evaluate(cfg: RevCConfig) -> RevCResult:
    c = cfg.clk_ns
    m2_low = CPU_PERIOD_NS * (1 - M2_HIGH_FRACTION)
    m2_high = CPU_PERIOD_NS * M2_HIGH_FRACTION
    low = cfg.cpu_low_clocks * c + cfg.latch_tpd_ns + cfg.pad_tpd_ns
    high = cfg.pad_tpd_ns + cfg.cpu_rom_access_ns + cfg.pad_tpd_ns + cfg.cpu_high_clocks * c
    ppu = cfg.ppu_clocks * c + cfg.latch_tpd_ns + 2 * cfg.pad_tpd_ns + cfg.chr_rom_access_ns
    return RevCResult(m2_low - low, m2_high - high, PPU_SLOT_NS - ppu)


PROFILES = {
    "measured_style": {},
    # Using the v3 optimisations (autopull/autopush, merged Hi-Z). PROPOSED.
    "proposed": {"cpu_low_clocks": 4, "cpu_high_clocks": 4, "ppu_clocks": 10},
}
CLOCKS = (150.0, 157.5, 171.8, 172.0)


def profile(name: str = "measured_style", **kw) -> RevCConfig:
    return RevCConfig(**{**PROFILES[name], **kw})


def sweep(clocks=CLOCKS, profile_name: str = "measured_style", **kw):
    return {m: evaluate(replace(profile(profile_name, **kw), sys_mhz=m)) for m in clocks}

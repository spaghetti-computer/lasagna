import unittest

from nespico.revb import RevBConfig, evaluate, profile, sweep


class RevBBudgetTests(unittest.TestCase):
    def test_nominal_assumptions_pass_all_clocks(self):
        for mhz, r in sweep().items():
            self.assertTrue(r.passed, (mhz, r))
            self.assertTrue(r.status_in_every_slot, mhz)

    def test_faster_clock_increases_margin(self):
        r = sweep()
        self.assertLess(r[150.0].ppu_slot_margin_ns, r[171.8].ppu_slot_margin_ns)

    def test_slow_chr_rom_moves_status_out_of_slot(self):
        r = evaluate(RevBConfig(chr_rom_access_ns=250.0))
        self.assertFalse(r.status_in_every_slot)
        self.assertGreater(r.irq_latency_worst_ns, 60_000)

    def test_slow_prg_rom_fails(self):
        self.assertFalse(evaluate(RevBConfig(cpu_rom_access_ns=340.0)).passed)

    def test_parallel_4016_does_not_change_timing(self):
        self.assertEqual(evaluate(RevBConfig()), evaluate(RevBConfig(parallel_4016=True)))


class MeasuredProfileTests(unittest.TestCase):
    def test_measured_totals_match_xiao_v1(self):
        cfg = profile("measured")
        self.assertEqual(cfg.cpu_low_total_clocks + cfg.cpu_high_total_clocks, 18)
        self.assertEqual(cfg.ppu_total_clocks, 21)

    def test_measured_passes_nominal_including_172(self):
        r = sweep()
        self.assertIn(172.0, r)
        for mhz, res in r.items():
            self.assertTrue(res.passed and res.status_in_every_slot, mhz)

    def test_proposed_profile_improves_margins(self):
        m, p = sweep(), sweep(profile_name="proposed")
        for mhz in m:
            self.assertGreater(p[mhz].ppu_slot_margin_ns, m[mhz].ppu_slot_margin_ns)
            self.assertGreater(p[mhz].cpu_m2_low_margin_ns, m[mhz].cpu_m2_low_margin_ns)

    def test_assumed_profile_unchanged(self):
        self.assertEqual(sweep(profile_name="assumed")[150.0], evaluate(RevBConfig()))


if __name__ == "__main__":
    unittest.main()

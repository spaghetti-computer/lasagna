import unittest

from nespico import revb, revc


class RevCTest(unittest.TestCase):
    def test_measured_style_passes_at_150(self):
        self.assertTrue(revc.evaluate(revc.profile()).passed)

    def test_proposed_passes_all_clocks(self):
        for r in revc.sweep(profile_name="proposed").values():
            self.assertTrue(r.passed)

    def test_revc_cpu_low_better_than_revb_measured(self):
        b = revb.evaluate(revb.profile("measured"))
        c = revc.evaluate(revc.profile())
        self.assertGreater(c.cpu_m2_low_margin_ns, b.cpu_m2_low_margin_ns)

    def test_higher_clock_increases_margin(self):
        s = revc.sweep()
        self.assertGreater(s[172.0].ppu_slot_margin_ns, s[150.0].ppu_slot_margin_ns)

    def test_slow_chr_rom_can_fail(self):
        self.assertFalse(revc.evaluate(revc.profile(chr_rom_access_ns=300)).passed)


if __name__ == "__main__":
    unittest.main()


class RevCDesignTest(unittest.TestCase):
    """P3 review item: no 5 V-driven net may reach GPIO40-47 (ADC pads are not 5 V tolerant)."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent / "hardware/kicad/revc/design.py"
        spec = importlib.util.spec_from_file_location("revc_design", p)
        cls.d = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.d)

    def test_adc_pins_not_on_5v_nets(self):
        d = self.d
        five_v = set()
        for c in d.COMPS:
            if c["ref"] in ("J3", "U2", "U3", "U4", "U5", "U6", "U7", "U8"):
                five_v |= set(c["nets"].values())
        five_v -= {"GND"}
        adc = {d.gp[g] for g in range(40, 48)}
        self.assertEqual(adc & five_v, set())

    def test_output_enables_pulled_inactive(self):
        d = self.d
        pulls = {}
        for c in d.COMPS:
            if c["sym"] == "R" and c["value"] == "10k":
                a, b = c["nets"]["1"], c["nets"]["2"]
                pulls.setdefault(a, set()).add(b); pulls.setdefault(b, set()).add(a)
        self.assertIn("+5V_CART", pulls["OUT_OE_N"])
        self.assertIn("+3V3", pulls["G_M2_N"])
        self.assertIn("+3V3", pulls["PPU_DEN_N"])
        self.assertIn("GND", pulls["CART_EN"])

    def test_i2c_expander_and_grove(self):
        d = self.d
        comps = {c["ref"]: c for c in d.COMPS}
        # I2C0 on GPIO44 (SDA, even) / GPIO45 (SCL, odd): same peripheral ((n // 2) % 2 == 0)
        self.assertEqual((d.gp[44], d.gp[45]), ("I2C_SDA", "I2C_SCL"))
        self.assertEqual({(44 // 2) % 2, (45 // 2) % 2}, {0})
        u = comps["U10"]["nets"]
        self.assertEqual((u["13"], u["12"], u["9"]), ("I2C_SDA", "I2C_SCL", "+3V3"))
        pads = {"PAD_CLK", "PAD_LATCH", "PAD1_D", "PAD2_D"}
        self.assertEqual(pads & set(d.gp.values()), set())          # pads no longer on direct GPIO
        self.assertTrue(pads <= set(u.values()))
        for j in ("J4", "J5"):
            self.assertEqual(comps[j]["nets"]["1"], "+3V3")          # pads powered at 3.3 V (no level shift needed)
        g = comps["J9"]["nets"]
        self.assertEqual([g[k] for k in "1234"], ["GND", "+3V3", "I2C_SDA", "I2C_SCL"])
        pu = {c["nets"]["1"] for c in d.COMPS if c["sym"] == "R" and c["value"] == "4.7k" and c["nets"]["2"] == "+3V3"}
        self.assertEqual(pu, {"I2C_SDA", "I2C_SCL"})
        tp = {n for n, _ in d.TPS}
        self.assertTrue({"SPARE_GP46", "SPARE_GP47"} <= tp)

    def test_rp2354_decoupling_per_hdg(self):
        """HDG 2.2.1: one 100 nF per supply pin (68/69 may share); DS 6.3.8.1: 2nd 4.7 uF on VOUT."""
        d = self.d
        caps = [c for c in d.COMPS if c["sym"] == "C"]
        v3 = [c for c in caps if (c["note"] == "decouple U1" or c["note"].startswith("decouple U1 ")) and c["nets"]["1"] == "+3V3"]
        self.assertEqual(len(v3), 10)          # IOVDD x8 + ADC_AVDD + (USB_OTP_VDD/QSPI_IOVDD shared)
        v11 = [c for c in caps if c["nets"]["1"] == "+1V1"]
        self.assertGreaterEqual(sum(c["value"] == "100nF" for c in v11), 2)
        self.assertEqual(sum(c["value"] == "4.7uF" for c in v11), 2)   # COUT + 2nd VOUT cap
        comps = {c["ref"]: c for c in d.COMPS}
        self.assertEqual(comps["R1"]["value"], "33"); self.assertEqual(comps["C7"]["value"], "4.7uF")
        self.assertEqual(comps["R2"]["value"], "1k"); self.assertEqual(comps["Y1"]["mpn"], "ABM8-272-T3")
        self.assertEqual({comps["R7"]["value"], comps["R8"]["value"]}, {"27"})
        self.assertEqual(comps["R4"]["nets"]["1"], "QSPI_SS")   # 1k to BOOTSEL button

    def test_minimal_copy_and_powerdown_guard(self):
        d = self.d
        comps = {c["ref"]: c for c in d.COMPS}
        self.assertEqual(comps["L1"]["nets"], {"1": "+1V1", "2": "VREG_LX"})   # dot pad = +1V1 as Minimal R4
        self.assertIn("RPi_AOTA", comps["L1"]["fp"])
        u = comps["U11"]["nets"]
        self.assertEqual((u["1"], u["2"], u["3"]), ("CART_EN", "GND", "+3V3"))
        self.assertEqual(d.gp[43], "CART_EN_G")                                 # GPIO isolated by 1k from CART_EN
        self.assertTrue(any(c["sym"] == "R" and set(c["nets"].values()) == {"CART_EN_G", "CART_EN"} for c in d.COMPS))

    def test_j3_hirose_cr22a_pin_map(self):
        j3 = {c["ref"]: c for c in self.d.COMPS}["J3"]
        self.assertIn("Hirose_CR22A-60D-2.54DS", j3["fp"])
        self.assertEqual(j3["nets"]["1"], "GND")           # NESdev: cart pin 1 = GND
        self.assertTrue(j3["nets"]["30"].startswith("+5V"))  # pin 30 = +5V; 31 (cart-present) NC
        self.assertNotIn("31", j3["nets"])

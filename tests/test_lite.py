"""LASAGNA2354 Lite (Core2350B module) design checks: design.py loaded with LASAGNA_LITE=1."""
import importlib.util, os, pathlib, unittest
D = pathlib.Path(__file__).resolve().parents[1] / "hardware/kicad/revc/design.py"

class LiteDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["LASAGNA_LITE"] = "1"
        try:
            spec = importlib.util.spec_from_file_location("design_lite", D)
            cls.d = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.d)
        finally:
            del os.environ["LASAGNA_LITE"]
        cls.c = {c["ref"]: c for c in cls.d.COMPS}

    # ---- helpers
    def gpio(self):
        """GPIO number -> net on the WeAct module."""
        pins = {p: n for p, n, _, _ in self.d.weact_pins()}
        return {int(pins[p][4:]): v for p, v in self.c["U1"]["nets"].items() if pins[p].startswith("GPIO")}

    def members(self, net):
        return [(r, p) for r, c in self.c.items() for p, v in c["nets"].items() if v == net]

    def test_module_is_weact(self):
        u1 = self.c["U1"]
        self.assertTrue(u1["mpn"].startswith("WeAct RP2350B"))
        self.assertEqual(u1["fp"], "NESPICO_RevC:WeAct_RP2350B_CoreBoard")
        self.assertEqual(len(u1["pins"]), 60)
        for r in ("L1", "Y1", "U9", "R7", "R8", "C30", "J7", "D1", "J1", "R5", "R6", "U12", "SW1", "SW2"):
            self.assertNotIn(r, self.c, r)
        tps = {t[0] for t in self.d.TPS}
        self.assertFalse({"BOOT_SW", "RUN", "SWCLK", "SWDIO", "USB_DM", "USB_DP", "CC1", "CC2"} & tps)
        used = {v for c in self.d.COMPS for v in c["nets"].values()}
        self.assertFalse({"BOOT_SW", "SWCLK", "SWDIO", "USB_DM", "USB_DP", "CC1", "CC2", "QSPI_SS"} & used)
        self.assertEqual(sorted(f"{c['ref']}.{k}" for c in self.d.COMPS for k, v in c["nets"].items() if v == "RUN"), ["J12.1", "U1.208"])

    def test_header_pinout_from_weact_schematic(self):
        p = {int(k): n for k, n, _, _ in self.d.weact_pins()}
        self.assertEqual([p[100 + i] for i in range(1, 9)], ["VBUS", "5V", "GND", "GND", "VREF", "GPIO0", "GPIO1", "GPIO2"])
        self.assertEqual((p[129], p[130]), ("GPIO23", "GPIO24"))
        self.assertEqual([p[200 + i] for i in range(1, 17)],
                         ["GND", "GND", "3V3_EN", "GND", "3V3", "3V3", "GPIO47", "RUN", "GPIO45", "GPIO46", "GPIO43", "GPIO44",
                          "GPIO41", "GPIO42", "GPIO39", "GPIO40"])
        self.assertEqual((p[229], p[230]), ("GPIO25", "GPIO26"))
        xy = {int(k): (x, y) for k, _, x, y in self.d.weact_pins()}
        self.assertAlmostEqual(xy[101][0] - xy[202][0], 38.10, places=2)        # outer rows (H1 odd, H2 even) 38.10 mm apart
        self.assertAlmostEqual(xy[101][1] - xy[129][1], 14 * 2.54, places=3)
        self.assertAlmostEqual(self.d.WEACT_L / 2 - xy[101][1], 1.778, places=3)  # pin 1 row 1.778 mm from the USB edge
        self.assertEqual((self.d.WEACT_W, self.d.WEACT_L), (41.148, 41.402))

    def test_power_from_vbus_not_diode_rail(self):
        n = self.c["U1"]["nets"]
        self.assertEqual(n["101"], "VBUS_IN")                                    # raw USB VBUS -> F1
        self.assertEqual(n["208"], "RUN")                                        # RUN -> DNP reset header J12 only
        for pad in ("102", "203", "105"):                                        # +5V after diode, 3V3_EN, VREF: NC
            self.assertNotIn(pad, n, pad)
        self.assertEqual((n["205"], n["206"]), ("+3V3", "+3V3"))
        self.assertEqual([n[k] for k in ("103", "104", "201", "202", "204")], ["GND"] * 5)
        self.assertEqual(self.c["F1"]["nets"], {"1": "VBUS_IN", "2": "VBUS_F"})
        self.assertEqual(sorted(r for r, _ in self.members("VBUS_IN")), ["F1", "JP2", "U1"])

    def test_no_net_on_h1_2_or_3v3_en(self):
        for c in self.d.COMPS:
            if c["ref"] == "U1":
                self.assertNotIn("102", c["nets"]); self.assertNotIn("203", c["nets"])
        pins = {p: n for p, n, _ in self.c["U1"]["pins"]}
        self.assertEqual((pins["102"], pins["203"]), ("5V", "3V3_EN"))

    def test_gpio_map(self):
        g = self.gpio()
        self.assertEqual(sorted(g), list(range(48)))
        self.assertEqual([g[i] for i in range(8)], [f"PADM{i}" for i in range(8)])
        self.assertEqual([g[i] for i in range(8, 14)], [f"GPA{i}" for i in range(8, 14)])
        self.assertEqual([g[i] for i in range(14, 18)], ["PPU_DEN_N", "G_RD", "G_WR_N", "PPU_ALE"])
        self.assertEqual([g[i] for i in range(25, 33)], [f"CADM{i}" for i in range(8)])
        self.assertEqual([g[i] for i in range(33, 40)], [f"GA{i}" for i in range(8, 15)])
        self.assertEqual([g[i] for i in range(40, 48)], ["G_RW", "G_ROMSEL_N", "G_M2_N", "CPU_ALE", "I2C_SDA", "I2C_SCL",
                                                         "SPARE_GP46", "SPARE_GP47"])
        self.assertEqual({g[i] for i in range(18, 25)}, {"IRQ_N", "CIRAM_A10", "CIRAM_CE_N", "OUT_OE_N", "CVBS_B0", "CVBS_B1", "CVBS_B2"})
        self.assertEqual((g[23], g[24]), ("OUT_OE_N", "CIRAM_A10"))            # GP23 = module KEY (pull-up): OE# wants one
        # every net of the old 48-pin map is still on a GPIO
        old = {"CART_EN_G": "OUT_OE_N"}
        self.assertEqual(sorted(g.values()), sorted(old.get(v, v) for v in self.d.gp.values()))

    def test_pio_windows(self):
        g = self.gpio(); inv = {v: k for k, v in g.items()}
        ppu = [f"PADM{i}" for i in range(8)] + [f"GPA{i}" for i in range(8, 14)] + ["PPU_DEN_N", "G_RD", "G_WR_N", "PPU_ALE"]
        cpu = [f"CADM{i}" for i in range(8)] + [f"GA{i}" for i in range(8, 15)] + ["G_RW", "G_ROMSEL_N", "G_M2_N", "CPU_ALE"]
        self.assertTrue(all(0 <= inv[n] <= 31 for n in ppu), "PPU group must sit in GPIO0-31")
        self.assertTrue(all(16 <= inv[n] <= 47 for n in cpu), "CPU group must sit in GPIO16-47")
        self.assertEqual(sorted(inv[n] for n in ppu), list(range(0, 18)))
        self.assertEqual(sorted(inv[n] for n in cpu), list(range(25, 44)))

    def test_gpio40_47_only_drive_ahct_inputs_or_3v3_parts(self):
        """GPIO40-47 are ADC pads (not 5 V tolerant): their nets may only reach AHCT inputs or 3.3 V-only parts,
        never a 245 B side, the cart slot, or a pull-up to a 5 V rail."""
        ahct_in = {"74AHCT573": {"LE", "OE_N"} | {f"D{i}" for i in range(8)},
                   "74AHCT541": {"OE1_N", "OE2_N"} | {f"A{i}" for i in range(1, 9)},
                   "74AHCT540": {"OE1_N", "OE2_N"} | {f"A{i}" for i in range(1, 9)},
                   "74AHCT245": {"DIR", "OE_N"}}                             # 245 A/B are bidirectional: never allowed
        three_v3_only = {"U10", "J9", "J10", "R52", "R53", "R60"}     # MCP23017/Grove/EXP (3V3), audio RC (DNP)
        five = {"+5V_LOGIC", "+5V_CART", "VBUS_IN", "VBUS_F"}
        g = self.gpio()
        for gp in range(40, 48):
            net = g[gp]
            for ref, pin in self.members(net):
                if ref == "U1" or ref.startswith("TP"): continue           # bare test pads
                c = self.c[ref]
                self.assertNotEqual(ref, "J3", f"GPIO{gp} {net} touches the cart")
                if c["sym"] in ahct_in:
                    pname = next(p[1] for p in c["pins"] if p[0] == pin)
                    self.assertIn(pname, ahct_in[c["sym"]], f"GPIO{gp} {net} -> {ref}.{pname} is not an AHCT input")
                elif c["sym"] == "R":
                    other = next(v for k, v in c["nets"].items() if k != pin)
                    self.assertNotIn(other, five, f"GPIO{gp} {net} pulled to a 5 V rail via {ref}")
                    self.assertTrue(other == "+3V3" or ref in three_v3_only, f"GPIO{gp} {net} -> {ref} -> {other}")
                else:
                    self.assertIn(ref, three_v3_only, f"GPIO{gp} {net} -> {ref}")
        self.assertNotIn("R63", self.c)                                           # zero exceptions: no GP46 -> cart path

    def test_pullups_to_3v3(self):
        for r, net in (("R31", "G_M2_N"), ("R32", "PPU_DEN_N"), ("R30", "OUT_OE_N"), ("R39", "IRQ_N")):
            self.assertEqual(self.c[r]["nets"], {"1": net, "2": "+3V3"}, r)
            self.assertFalse(self.c[r]["dnp"], r)
        for c in self.d.COMPS:                                                    # no GPIO net is pulled to a 5 V rail
            if c["sym"] == "R" and set(c["nets"].values()) & {"+5V_LOGIC", "+5V_CART"}:
                self.assertFalse(set(c["nets"].values()) & set(self.gpio().values()), c["ref"])

    def test_series_arrays_and_e9_pulldown(self):
        for r in [f"R{i}" for i in (*range(10, 18), *range(20, 28))]: self.assertNotIn(r, self.c)
        self.assertEqual(self.c["RN1"]["nets"], {"1": "CADM3", "8": "CAD3", "2": "CADM2", "7": "CAD2", "3": "CADM1", "6": "CAD1", "4": "CADM0", "5": "CAD0"})
        self.assertEqual((self.c["RN4"]["nets"]["1"], self.c["RN4"]["nets"]["8"]), ("PADM7", "PAD7"))
        self.assertEqual(self.d.LCSC[self.c["RN1"]["mpn"]][0], "C25508")
        r41 = self.c["R41"]; self.assertFalse(r41["dnp"])                      # E9 (A2): <= 8.2k pull-down fitted
        self.assertEqual((r41["value"], r41["nets"]), ("5.1k", {"1": "CIRAM_A10", "2": "GND"}))
        self.assertEqual(self.gpio()[24], "CIRAM_A10")

    def test_latch_pin_swap_is_consistent(self):
        for u, d, q in (("U2", "CAD", "CA"), ("U3", "PAD", "PA")):
            n = self.c[u]["nets"]
            for j in range(8):
                self.assertEqual((n[str(2 + j)], n[str(19 - j)]), (f"{d}{7 - j}", f"{q}{7 - j}"), u)

    def test_vbus_diode_and_bypass(self):
        self.assertEqual(self.c["D2"]["nets"], {"1": "+5V_LOGIC", "2": "VBUS_F"})    # K = rail, A = connector side
        self.assertEqual(self.d.LCSC["SS34"][0], "C8678")
        self.assertEqual(set(self.c["JP1"]["nets"].values()), {"VBUS_F", "+5V_LOGIC"})
        self.assertEqual(set(self.c["JP2"]["nets"].values()), {"VBUS_IN", "VBUS_F"})
        self.assertIn("Open", self.c["JP2"]["fp"])
        self.assertFalse(self.c["F1"]["dnp"]); self.assertEqual(self.d.LCSC[self.c["F1"]["mpn"]][0], "C66452")
        self.assertTrue(self.c["JP1"]["dnp"]); self.assertIn("Bridged", self.c["JP1"]["fp"])
        self.assertTrue(self.c["D2"]["dnp"] and self.c["D2"].get("nofit"))

    def test_dnp_full_features(self):
        for r in ("J6", "R90", "R91", "R92", "U10", "J9", "J4", "J5", "R42", "R43", "R51", "R52", "R53", "C27", "J10"):
            self.assertTrue(self.c[r]["dnp"] and self.c[r].get("nofit"), r)
        g = self.gpio()
        self.assertEqual([g[i] for i in (44, 45, 46, 47)], ["I2C_SDA", "I2C_SCL", "SPARE_GP46", "SPARE_GP47"])
        self.assertEqual({g[i] for i in (18, 19, 20)}, {"CVBS_B0", "CVBS_B1", "CVBS_B2"})

    def test_adc_pins_not_on_5v_nets(self):
        five = set()
        for r in ("J3", "U2", "U3", "U4", "U5", "U6", "U7", "U8"):
            five |= {v for k, v in self.c[r]["nets"].items()
                     if not (self.c[r]["sym"] in ("74AHCT573", "74AHCT541", "74AHCT540") and k in [str(i) for i in range(1, 10)] + ["11", "19"])
                     and not (self.c[r]["sym"] == "74AHCT245" and k in ("1", "19"))}             # AHCT inputs are fine
        five -= {"GND"}
        for gp, net in self.gpio().items():
            if gp >= 40: self.assertNotIn(net, five, gp)

    def test_grove_seeed_pin_order(self):
        j9 = self.c["J9"]
        self.assertEqual(j9["nets"], {"1": "I2C_SCL", "2": "I2C_SDA", "3": "+3V3", "4": "GND", "MP": "GND"})
        self.assertTrue(j9["dnp"] and j9.get("nofit"))
        g = self.gpio()
        self.assertEqual((g[44], g[45]), ("I2C_SDA", "I2C_SCL"))

    def test_audio_out_dnp_chain(self):
        c = self.c
        self.assertEqual(c["R60"]["nets"], {"1": "SPARE_GP46", "2": "AUD_F"}); self.assertEqual(c["R60"]["value"], "1k")
        self.assertEqual(c["C60"]["nets"], {"1": "AUD_F", "2": "GND"}); self.assertEqual(c["C60"]["value"], "10nF")
        self.assertEqual(c["C61"]["nets"], {"1": "AUD_F", "2": "AUD_OUT"}); self.assertEqual(c["C61"]["value"], "10uF")
        self.assertEqual(c["R61"]["nets"], {"1": "AUD_OUT", "2": "GND"}); self.assertEqual(c["R61"]["value"], "10k")
        self.assertEqual(c["J11"]["nets"], {"1": "AUD_OUT", "2": "GND"})
        self.assertEqual((c["J11"]["fp"], c["J11"]["mpn"]), (c["J6"]["fp"], c["J6"]["mpn"]))     # same Akizuki 112477 RCA
        fc = 1 / (2 * 3.14159 * 1e3 * 10e-9); self.assertTrue(14e3 < fc < 18e3)
        for r in ("R60", "C60", "C61", "R61", "R62", "J11"):
            self.assertTrue(c[r]["dnp"] and c[r].get("nofit"), r)
        self.assertEqual(self.d.LCSC["10nF"][0], "C57112")
        for r in ("R60", "C60", "C61", "R61", "R62"): self.assertIn(c[r]["mpn"], self.d.LCSC, r)
        self.assertEqual(c["J10"]["nets"]["2"], "SPARE_GP46")                     # GPIO46 still on the EXP header
        g = self.gpio()
        self.assertEqual(g[46], "SPARE_GP46")
        aud = {"AUD_F", "AUD_OUT", "CART_AUD_IN", "CART_AUD_OUT"}
        self.assertFalse(aud & {g[47]}); self.assertEqual(g[47], "SPARE_GP47")   # GPIO47 unused by audio

    def test_cart_expansion_audio_pins(self):
        j3 = self.c["J3"]["nets"]                                                  # NESdev: 45 = audio from 2A03 (to cart), 46 = to RF (from cart)
        self.assertNotIn("45", j3); self.assertEqual(j3["46"], "CART_AUD_OUT")
        self.assertNotIn("31", j3)
        self.assertEqual(self.c["R62"]["nets"], {"1": "CART_AUD_OUT", "2": "AUD_F"})
        for n in ("CART_AUD_IN", "CART_AUD_OUT"):                                 # cart audio never touches a GPIO directly
            self.assertNotIn(n, self.c["U1"]["nets"].values())

    def test_placement(self):
        src = (D.parent / "gen_pcb.py").read_text()
        for r in ("J11", "R60", "C60", "C61", "R61", "R62", "J4", "J5", "J10", "J9", "F1", "JP2", "D2", "JP1", "RN1", "RN4"):
            self.assertRegex(src, rf'"{r}": \(', r)
        self.assertIn("H = 67.0", src)
        self.assertIn("MOD_X, MOD_Y = 50.0, H - design.WEACT_L / 2", src)   # module centred, USB-C edge flush with y = 67
        self.assertIn('ICS = ["U6", "U2", "U4", "U8", "U7", "U3", "U5"]', src)
        self.assertNotIn("DO NOT USE MODULE FPC", src.split("if LITE:   # WeAct")[1])
        for s in ("LIFT R16", "NO PSRAM", "UNPLUG USB", "MADE IN KOBE", "JLCJLCJLCJLC", "SPAGHETTI COMPUTER"):
            self.assertIn(s, src)

if __name__ == "__main__":
    unittest.main()


import json, re, shutil, subprocess, tempfile
LITE_DIR = pathlib.Path(__file__).resolve().parents[1] / "hardware/kicad/revc_lite"
LITE_SCH = LITE_DIR / "LASAGNA2354_Lite.kicad_sch"
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures/lite_netlist_golden.json"

class LiteSchematicDrawnTest(unittest.TestCase):
    """The Lite schematic is a drawn hierarchical sheet set, not a label dump."""
    def test_hierarchy_and_wires(self):
        root = LITE_SCH.read_text()
        self.assertIn('(paper "A3")', root)
        subs = re.findall(r'\(property "Sheetfile" "([^"]+)"', root)
        self.assertEqual(len(subs), 7)
        wires = juncs = 0
        for s in subs:
            t = (LITE_DIR / s).read_text()
            self.assertRegex(t, r'\(paper "A[34]"\)')
            self.assertIn("(rectangle", t)                  # block frames
            w = t.count("(wire (pts"); wires += w; juncs += t.count("(junction")
            self.assertGreater(w, 20, s)
        self.assertGreater(wires, 400)
        self.assertGreater(juncs, 15)
        self.assertNotIn("(label ", "".join((LITE_DIR / s).read_text() for s in subs))  # sub-sheets use hier labels

    @unittest.skipUnless(shutil.which("kicad-cli"), "kicad-cli not installed")
    def test_netlist_matches_golden(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "lite.net"
            subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", str(out), str(LITE_SCH)], check=True, capture_output=True)
            t = out.read_text()
        nets = {}
        for blk in re.split(r'\(net \(code ', t)[1:]:
            name = re.search(r'\(name "((?:[^"\\]|\\.)*)"', blk).group(1)
            nodes = sorted(f"{a}:{b}" for a, b in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"', blk) if not a.startswith("#"))
            if nodes: nets[name] = nodes
        self.assertEqual(nets, json.loads(GOLDEN.read_text()))

    @unittest.skipUnless(shutil.which("kicad-cli"), "kicad-cli not installed")
    def test_erc_clean(self):
        with tempfile.TemporaryDirectory() as td:
            rpt = pathlib.Path(td) / "erc.rpt"
            subprocess.run(["kicad-cli", "sch", "erc", "-o", str(rpt), str(LITE_SCH)], check=True, capture_output=True)
            self.assertRegex(rpt.read_text(), r"ERC messages: 0\s+Errors 0")


class LitePopulationTest(unittest.TestCase):
    """Minimal (dump-only) build works with every option unfitted; full build adds every feature."""
    @classmethod
    def setUpClass(cls):
        LiteDesignTest.setUpClass.__func__(cls)
    OPTIONS = {"U10", "R51", "R52", "R53", "C27", "J9", "J4", "J5", "R42", "R43",          # pads + Grove
               "J6", "R90", "R91", "R92", "J11", "R60", "R61", "R62", "C60", "C61",        # CVBS, audio
               "J10", "J12", "D2"}
    def test_options_are_dnp(self):
        for r in self.OPTIONS & set(self.c):
            self.assertTrue(self.c[r]["dnp"], r)
    def test_minimal_build_nets_complete(self):
        mini = [c for c in self.d.COMPS if c["ref"] not in self.OPTIONS and not c["ref"].startswith(("TP", "H"))]
        refs = {c["ref"] for c in mini}
        for need in ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "J3", "F1", "C1", "RN1", "RN2", "RN3", "RN4", "R41"):
            self.assertIn(need, refs)
        drivers = {}
        for c in mini:
            for k, v in c["nets"].items(): drivers.setdefault(v, set()).add(c["ref"])
        # every logic IC input and every cart-side signal stays connected to something else in the minimal build
        for u in ("U2", "U3", "U4", "U5", "U6", "U7", "U8"):
            for k, v in self.c[u]["nets"].items():
                self.assertGreater(len(drivers[v]), 1, f"{u}.{k} {v} floats in minimal build")
        # +5V_LOGIC must be reachable without D2: JP1 (bridged by default) closes VBUS_F -> +5V_LOGIC
        self.assertIn("JP1", refs); self.assertIn("JP2", refs)

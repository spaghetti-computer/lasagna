#!/usr/bin/env python3
"""Create LASAGNA2354_RevC.kicad_pcb: footprints + nets + placement (routing done separately)."""
import pcbnew, design, gen_sch
from pathlib import Path
HERE = Path(__file__).parent
FPROOT = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM
OX, OY, W, H = 100.0, 100.0, 100.0, 62.0

def load(fpid):
    lib, name = fpid.split(":")
    path = str(HERE / "NESPICO_RevC.pretty") if lib == "NESPICO_RevC" else f"{FPROOT}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

# Placement: symmetric about x=50. Famicom slot on the TOP edge: cart pins 1-30 on row y=SLOT_Y, 31-60 on
# SLOT_Y-5.08, left->right. CPU signals (2-14, 32-44) are in the LEFT half, PPU (17-29, 47-60) in the RIGHT half.
# Everything in P is LOCKED for Quilter. All other parts are placed outside the outline for Quilter to place.
SLOT_X0 = 50 - 29 * 2.54 / 2
SLOT_Y = 7.8                 # cart pins 1-30 row; 31-60 row is 5.08 mm nearer the top edge (Hirose CR22A)
IC_Y, U1_Y, FRONT_Y = 18.0, 37.0, 52.0
P = {
    "J3": (SLOT_X0, SLOT_Y, 0),
    "U1": (50, U1_Y, 0),
    "SW1": (36, FRONT_Y, 0), "SW2": (64, FRONT_Y, 0),       # front (user-facing) edge, symmetric
    "J1": (4.5, 30.5, 270),            # USB-C, left short edge (x snapped flush below)
    "J6": (100 - 6.9, 30.5, 90),               # RCA, right short edge (x snapped flush below)
    "H1": (3.7, 4.5, 0), "H2": (96.3, 4.5, 0), "H3": (4.5, 57.5, 0), "H4": (95.5, 57.5, 0),
    "D1": (94.5, 46.5, 0),           # CART power LED under the RCA, labelled CART
    "U10": (COLS_B2 := 50 + (1 - 3) * 13, 43.0, 90),   # MCP23017, grid B2 (under column 2), same rotation as row A
    "J9": (5.0, 43.0, 270),          # Grove I2C, left edge under the USB-C
    "J4": (9.5, FRONT_Y, 90), "J5": (90.5 - 6 * 2.54, FRONT_Y, 90),
    "J7": (50 - 2.54, FRONT_Y + 2.5, 90),   # moved down: Minimal-style crystal sits 13.9 mm below U1
}
ICS = ["U2", "U4", "U6", "U8", "U7", "U5", "U3"]     # row A right under the slot keepout: CPU | centre | PPU
COLS = [50 + (i - 3) * 13 for i in range(7)]
for u, x in zip(ICS, COLS):
    P[u] = (x, IC_Y, 90)    # horizontal: long axis along X, all same orientation
# Parts placed relative to U1 (dx, dy, rot), per RP2350 hardware design guide: VREG L/C tight, crystal next to XIN/XOUT.
U1REL = {
    # Regulator + USB R + crystal: RP2350 Minimal R4 (QFN-60) offsets mapped to RP2354B QFN-80. The VREG/USB pins keep
    # the same order and 0.4 mm pitch (QFN-60 46..52 -> QFN-80 61..67), so the translation is (+1.0, -1.5) mm.
    # Crystal pins (QFN-60 21/22 -> QFN-80 30/31): translation (+0.6, +1.5) mm.
    "L1": (3.0, -8.7, 0), "C6": (3.0, -7.05, 0), "C5": (3.0, -6.11, 0), "C7": (5.2, -6.55, -90), "R1": (5.2, -8.4, -90),
    "R7": (-0.1, -8.9, -90), "R8": (0.9, -8.9, -90),
    "Y1": (0.6, 13.9, 0), "R2": (0.2, 8.4, -90), "C8": (-0.8, 10.5, 180), "C9": (2.18, 10.5, 0),
    "C30": (1.4, 8.38, -90), "C29": (-1.2, 7.58, -90),
    # remaining supply decoupling (not part of the copied section)
    "C22": (-5.0, -6.9, 0), "C32": (-2.4, -7.4, 90),
    "C17": (-7.4, -2.2, 0), "C23": (-7.4, -0.2, 0), "C18": (-7.4, 1.8, 0),   # IOVDD5, DVDD10, IOVDD15
    "C21": (7.4, -3.8, 0), "C24": (7.4, -1.8, 0), "C20": (7.4, 0.2, 0), "C19": (7.4, 3.8, 0),  # 60, DVDD51, 50, 41
    "C28": (-5.6, 7.8, 90), "C31": (10.6, -5.0, 0),
}
DECAP = {"C27": "U10", "C10": "U2", "C11": "U3", "C12": "U4", "C13": "U5", "C14": "U6", "C15": "U7", "C16": "U8"}
NEAR_J6 = {"R90": (-6.0, 11.6, 90), "R91": (-4.0, 11.6, 90), "R92": (-2.0, 11.6, 90)}   # row under the RCA
# Aesthetic pass: 33R AD series arrays, one row per bus, 2.54 mm pitch, exact mirror about x=50
RARR_Y, RARR_PITCH = 31.0, 2.0
for i in range(8):
    xc = COLS[1] + (i - 3.5) * RARR_PITCH          # CPU bus centred under column 2 (U4)
    P[f"R{10+i}"] = (xc, RARR_Y, 90)
    P[f"R{20+i}"] = (100 - xc, RARR_Y, 90)         # PPU bus mirrored under column 6 (U5)
TP_Y, TP_PITCH, TP_LBL_Y = 57.0, 3.5, 59.4      # one bed-of-nails row on the front edge (1.5x 2.54 grid)
for i in range(len(design.TPS)):
    P[f"TP{i+1}"] = (50 + (i - (len(design.TPS) - 1) / 2) * TP_PITCH, TP_Y, 0)
FIDS = [(6.0, 22.0), (96.5, 12.5), (96.5, 49.0)]  # asymmetric: 2 top, 1 bottom-right
CORNER_R = 3.0
COORD = {u: f"A{i+1}" for i, u in enumerate(ICS)}
LOCKED = set(P) | set(U1REL) | set(DECAP) | set(NEAR_J6)
LITE = design.LITE
OUTD, NAME = (HERE.parent / "revc_lite", "LASAGNA2354_Lite") if LITE else (HERE, "LASAGNA2354_RevC")
if LITE:   # WeAct Studio RP2350B Core Board (41.148 x 41.402) centred on the front edge, USB-C flush (2026-10-17 port)
    H = 67.0
    MOD_X, MOD_Y = 50.0, H - design.WEACT_L / 2           # module centre: x 29.43-70.57, y 25.60-67.00
    FIDS = []                                             # hand-built: fiducials are only useful for PCBA
    P["H3"] = (4.5, H - 4.5, 0); P["H4"] = (95.5, H - 4.5, 0)
    for r in ("D1", "J7", "SW1", "SW2"): P.pop(r, None)
    U1REL.clear(); NEAR_J6.clear()
    P["U1"] = (MOD_X, MOD_Y, 0)
    # Row A (y=18): CPU group left (U6 A8-14, U2 A0-7 latch, U4 data), U8 centre, PPU group right (U7 A8-13, U3 latch, U5 data).
    # 573/541/540 at 90 deg (inputs face the module, outputs face the slot); 245s at 270 deg (A = cart side up).
    ICS = ["U6", "U2", "U4", "U8", "U7", "U3", "U5"]
    for u, x in zip(ICS, COLS):
        P[u] = (x, IC_Y, 270 if u in ("U4", "U5") else 90)
    # pulls in the column gaps of row A, on the nets they hold (R31 G_M2_N / R30 OE#, R39 IRQ / R41 CIRAM_A10, R32 DEN)
    P.update({"R31": (42.3, IC_Y, 90), "R30": (44.7, IC_Y, 90), "R39": (55.3, IC_Y, 90), "R41": (57.7, IC_Y, 90),
              "R32": (69.5, IC_Y, 90)})
    # 33R packs hugging the headers they serve: RN1/RN2 left of H2 (CADM0-7 = GP25-32), RN3/RN4 right of H1 (PADM0-7 = GP0-7)
    P.update({"RN1": (26.4, 31.0, 180), "RN2": (26.4, 36.0, 180), "RN3": (73.6, 57.1, 0), "RN4": (73.6, 52.5, 0)})
    # power: H1-1 VBUS (69.05, 65.22) -> F1 (JP2 bypass) -> D2 DNP / JP1 bridged -> +5V_LOGIC, C1 bulk
    P.update({"F1": (74.6, 64.8, 0), "JP2": (74.6, 61.6, 0), "D2": (80.6, 64.8, 180), "JP1": (80.6, 61.6, 0),
              "C1": (86.0, 64.8, 90)})
    # DNP options. Right edge: CVBS RCA J6 + DAC (GP18-20 exit H1 at y 34.7-37.3), audio RCA J11 + RC chain.
    P.update({"J6": (100 - 6.9, 33.0, 90), "R90": (80.4, 35.0, 90), "R91": (82.0, 35.0, 90), "R92": (84.0, 35.0, 90),
              "J11": (100 - 6.9, 49.0, 90),
              "R60": (80.4, 45.0, 90), "C60": (82.0, 45.0, 90), "C61": (84.0, 45.0, 90),
              "R61": (80.4, 50.0, 90), "R62": (82.0, 50.0, 90)})
    # Left: Grove J9 (edge), MCP23017 U10 + pulls, EXP J10 beside H2 (GP46/47), pads J4/J5 on the front edge
    P.update({"J9": (6.0, 52.0, 270), "U10": (16.6, 51.4, 90),
              "R51": (27.3, 49.5, 90), "R52": (27.3, 52.5, 90), "R53": (27.3, 55.5, 90),
              "J10": (24.6, 46.4, 0), "J12": (24.6, 40.0, 0),
              "J5": (11.9, 60.9, 90), "J4": (11.9, 64.8, 90), "R43": (13.5, 57.8, 0), "R42": (20.7, 57.8, 0)})
    # test points: 3 rows x 8 at 2.54 mm under the module's far end (bare THT pads, no height; probe from the back)
    TP_COLS, TP_ROWS, TP_PITCH, TP_XC = 8, (27.0, 30.9, 34.8), 3.2, 48.5   # 1.5 mm left: wider right lane (PPU A8-13)
    for i in range(len(design.TPS)):
        r, k = divmod(i, TP_COLS)
        P[f"TP{i+1}"] = (TP_XC + (k - (TP_COLS - 1) / 2) * TP_PITCH, TP_ROWS[r], 0)
    TP_LBL_DY = 1.95
    _refs = {c["ref"] for c in design.COMPS}
    for d in (P, DECAP):
        for r in [r for r in d if r not in _refs]: d.pop(r)
    COORD = {u: f"A{i+1}" for i, u in enumerate(ICS)}
    LOCKED = set(P) | set(DECAP)

ROLE = {"U2": "CPU A0-7 LATCH", "U4": "CPU D XCVR", "U6": "OUT BUF", "U8": "INV M2/PA13/RD",
        "U7": "OUT BUF", "U5": "PPU D XCVR", "U3": "PPU A0-7 LATCH"}
def design_part(ref):
    return next(c["mpn"] for c in design.COMPS if c["ref"] == ref)

def weact_footprint():
    """NESPICO_RevC:WeAct_RP2350B_CoreBoard from design.weact_pins() (official schematic H1/H2 + dimension drawing)."""
    W2, L2 = design.WEACT_W / 2, design.WEACT_L / 2
    L = ['(footprint "WeAct_RP2350B_CoreBoard" (version 20240108) (generator "lasagna") (layer "F.Cu")',
         '  (descr "WeAct Studio RP2350B Core Board V1.0, 41.148 x 41.402 mm, 2x 2x15 2.54 mm headers (outer rows 38.10 apart). '
         'Pad 1xx = H1 pin xx (VBUS/5V/GND/GND/VREF/GP0-24), 2xx = H2 pin xx (GND/GND/3V3_EN/GND/3V3/3V3/GP47/RUN/GP45-26). '
         'Origin = module centre, +y = USB-C edge. Verified against WeActStudio HDK RP2350B_SCH.pdf, RP2350B_PINOUT.png, dimension drawing.")',
         '  (tags "WeAct RP2350B core board module")', '  (attr through_hole)',
         f'  (property "Reference" "U1" (at 0 {-L2 + 2.6:.3f} 0) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))))',
         '  (property "Value" "WeAct RP2350B" (at 0 -16 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    def rect(x0, y0, x1, y1, layer, w=0.1):
        L.append(f'  (fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))')
    def line(x0, y0, x1, y1, layer, w=0.12):
        L.append(f'  (fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))')
    def ftxt(s, x, y, layer="F.Fab", sz=0.8):
        L.append(f'  (fp_text user "{s}" (at {x:.3f} {y:.3f} 0) (layer "{layer}") (effects (font (size {sz} {sz}) (thickness {sz*0.15:.2f}))))')
    rect(-W2, -L2, W2, L2, "F.Fab")
    rect(-W2 - 0.25, -L2 - 0.25, W2 + 0.25, L2, "F.CrtYd", 0.05)       # USB edge = board edge
    s = 0.15                                                               # silk: 3 sides (front edge = board edge)
    line(-W2 - s, -L2 - s, W2 + s, -L2 - s, "F.SilkS"); line(-W2 - s, -L2 - s, -W2 - s, L2 - 0.6, "F.SilkS")
    line(W2 + s, -L2 - s, W2 + s, L2 - 0.6, "F.SilkS")
    # pin-1 marks (H1-1 VBUS, H2-1 GND) beside the USB end
    for x in (W2 + 0.9,):                                                  # H2-1 is marked by its square pad
        L.append(f'  (fp_circle (center {x:.3f} {L2 - 1.778:.3f}) (end {x + 0.3:.3f} {L2 - 1.778:.3f}) (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))')
    # module-side areas to keep clear (fab layer): RP2350B QFN, bottom-side PSRAM/flash2 SOP-8 (U7, never fit), SWD 1x4, USB-C shell legs
    rect(-7.3, -11.1, 7.7, 3.9, "F.Fab"); ftxt("RP2350B (keep clear)", 0.2, -3.6)
    rect(3.7, 4.8, 13.1, 14.3, "F.Fab"); ftxt("PSRAM U7 (bottom) NEVER FIT", 8.4, 9.6, sz=0.6)
    rect(3.2, -11.7, 13.4, -9.1, "F.Fab"); ftxt("SWD 1x4 (no pins down)", 8.3, -12.5, sz=0.6)
    rect(-5.4, 13.2, 5.4, L2 + 0.3, "F.Fab"); ftxt("USB-C (shell legs)", 0, 16.6, sz=0.6)
    ftxt("H1 GP0-24", 17.8, -22.0 + 1.0, sz=0.7); ftxt("H2 GP25-47", -17.8, -22.0 + 1.0, sz=0.7)
    for pad, nm, x, y in design.weact_pins():
        shape = "rect" if pad in ("101", "201") else "circle"
        L.append(f'  (pad "{pad}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    L.append(')')
    (HERE / "NESPICO_RevC.pretty" / "WeAct_RP2350B_CoreBoard.kicad_mod").write_text("\n".join(L) + "\n")

def main():
    if LITE: weact_footprint()
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nets = {}
    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(b, "/" + n); b.Add(ni); nets[n] = ni
        return nets[n]
    others = []
    for c in design.COMPS:
        fp = load(c["fp"])
        fp.SetReference(c["ref"]); fp.SetValue(c["value"]); fp.SetPath(pcbnew.KIID_PATH("/" + gen_sch.U(c["ref"])))
        lc = design.LCSC.get(c["mpn"])
        for k, v in (("LCSC", lc[0] if lc else ""), ("MPN", c["mpn"])):
            fld = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER if hasattr(pcbnew, "FIELD_T_USER") else 0, k) if False else None
            fp.SetField(k, v) if hasattr(fp, "SetField") else None
        if c["dnp"]:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for pad in fp.Pads():
            n = c["nets"].get(pad.GetNumber())
            if n: pad.SetNet(net(n))
            elif pad.GetNumber():
                pn = next((p[1] for p in c["pins"] if p[0] == pad.GetNumber()), pad.GetNumber())
                nm = f"unconnected-({c['ref']}-Pad{pad.GetNumber()})" if pn == pad.GetNumber() else f"unconnected-({c['ref']}-{pn}-Pad{pad.GetNumber()})"
                ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni); pad.SetNet(ni)
        if c["ref"].startswith("H") or c["ref"].startswith("TP"):
            fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM & ~pcbnew.FP_BOARD_ONLY); fp.Reference().SetVisible(False)
        b.Add(fp)
        if c["ref"] in P:
            x, y, rot = P[c["ref"]]
            fp.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); fp.SetOrientationDegrees(rot)
        elif c["ref"] not in LOCKED:
            others.append(fp)
    # unlocked parts: grid OUTSIDE the outline (below the board)
    for k, fp in enumerate(sorted(others, key=lambda f: f.GetReference())):
        big = {}
        r = fp.GetReference()
        x, y, rot = big[r] if r in big else (3 + 8.0 * (k % 12), 70 + 8.0 * (k // 12), 0)
        fp.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); fp.SetOrientationDegrees(rot)
    F = {f.GetReference(): f for f in b.GetFootprints()}
    def at(ref, x, y, rot):
        F[ref].SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); F[ref].SetOrientationDegrees(rot)
    for r, (dx, dy, rot) in U1REL.items():
        at(r, 50 + dx, U1_Y + dy, rot)
    for cref, u in DECAP.items():           # 100 nF next to VCC pin 20, outward (perpendicular to the IC long axis)
        p = F[u].FindPadByNumber("9" if u == "U10" else "20").GetPosition(); cy = F[u].GetPosition().y
        sgn = 1 if p.y > cy else -1
        at(cref, pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY + sgn * 2.6, 0)
    def bbox(ref):
        bb = F[ref].GetBoundingBox(False)
        return [pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
    # P7: USB-C mouth / RCA body flush with the short edges (0.5 mm overhang)
    for jp in ("JP1", "JP2"):
        if jp in F: F[jp].SetAttributes(F[jp].GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM)   # match the schematic symbol
    if "J1" in F: l = bbox("J1")[0] - OX; F["J1"].Move(pcbnew.VECTOR2I(MM(-0.5 - l), 0))
    j6 = F["J6"].GetPosition() if "J6" in F else None
    for rr, (dx, dy, rot) in NEAR_J6.items():
        at(rr, pcbnew.ToMM(j6.x) - OX + dx, pcbnew.ToMM(j6.y) - OY + dy, rot)
    # P2: no signals under the crystal on B.Cu (rule area)
    yx, yy = 50.6, U1_Y + 13.9
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayer(pcbnew.B_Cu)
    z.SetDoNotAllowFootprints(False); z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False)
    z.SetZoneName("XTAL_NO_SIGNAL_BCU"); ol = z.Outline(); ol.NewOutline()
    for px, py in ((yx - 2.4, yy - 1.9), (yx + 2.4, yy - 1.9), (yx + 2.4, yy + 1.9), (yx - 2.4, yy + 1.9)):
        ol.Append(MM(OX + px), MM(OY + py))
    if not LITE: b.Add(z)                    # Lite: crystal is on the module
    # P6: planned bottom GND pour (unfilled; Quilter / final fill)
    g = pcbnew.ZONE(b); g.SetLayer(pcbnew.B_Cu); g.SetNet(net("GND")); g.SetZoneName("GND_POUR_BCU")
    g.SetLocalClearance(MM(0.3)); g.SetMinThickness(MM(0.25))
    ol = g.Outline(); ol.NewOutline()
    for px, py in ((0.5, 0.5), (99.5, 0.5), (99.5, H - 0.5), (0.5, H - 0.5)):
        ol.Append(MM(OX + px), MM(OY + py))
    b.Add(g)
    for fp in b.GetFootprints():
        fp.SetLocked(fp.GetReference() in LOCKED)
    # keepout around the slot (both layers): no footprints, no vias, no pours; tracks allowed for the slot's own fanout
    sx0, sx1 = 50 - 84.84 / 2, 50 + 84.84 / 2                   # Hirose CR22A-60 body A=84.84
    by1 = SLOT_Y - 2.54 + 9.5 / 2                                 # body bottom edge (D=9.5)
    for i, (x0, y0, x1, y1) in enumerate([(sx0, by1 + 0.3, sx1, by1 + 1.5)]):
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        z.SetDoNotAllowFootprints(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowTracks(False); z.SetDoNotAllowPads(False); z.SetZoneName(f"SLOT_KEEPOUT_{i}")
        ol = z.Outline(); ol.NewOutline()
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(MM(OX + px), MM(OY + py))
        b.Add(z)
    # outline: rounded corners R=CORNER_R
    R = CORNER_R
    def seg(x0, y0, x1, y1):
        t = pcbnew.PCB_SHAPE(b); t.SetShape(pcbnew.SHAPE_T_SEGMENT); t.SetLayer(pcbnew.Edge_Cuts); t.SetWidth(MM(0.1))
        t.SetStart(pcbnew.VECTOR2I(MM(OX + x0), MM(OY + y0))); t.SetEnd(pcbnew.VECTOR2I(MM(OX + x1), MM(OY + y1))); b.Add(t)
    def arc(cx, cy, sx, sy, ang, layer=pcbnew.Edge_Cuts, w=0.1):
        t = pcbnew.PCB_SHAPE(b); t.SetShape(pcbnew.SHAPE_T_ARC); t.SetLayer(layer); t.SetWidth(MM(w))
        t.SetCenter(pcbnew.VECTOR2I(MM(OX + cx), MM(OY + cy))); t.SetStart(pcbnew.VECTOR2I(MM(OX + sx), MM(OY + sy)))
        t.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True); b.Add(t)
    seg(R, 0, W - R, 0); seg(W, R, W, H - R); seg(W - R, H, R, H); seg(0, H - R, 0, R)
    arc(W - R, R, W - R, 0, 90); arc(W - R, H - R, W, H - R, 90); arc(R, H - R, R, H, 90); arc(R, R, 0, R, 90)
    # mounting-hole keep-out rings (no tracks/vias within 4.0 mm of the hole centre; GND pad itself is allowed)
    for ref in ("H1", "H2", "H3", "H4"):
        hx, hy, _ = P[ref]
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        z.SetDoNotAllowFootprints(False); z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False)
        z.SetZoneName(f"MH_KEEPOUT_{ref}"); ol = z.Outline(); ol.NewOutline()
        import math
        for k in range(24):
            ol.Append(MM(OX + hx + 4.0 * math.cos(k * math.pi / 12)), MM(OY + hy + 4.0 * math.sin(k * math.pi / 12)))
        b.Add(z)
    # fiducials (board-only, 1 mm copper / 2 mm mask)
    for i, (fx, fy) in enumerate(FIDS):
        f = pcbnew.FootprintLoad(f"{FPROOT}/Fiducial.pretty", "Fiducial_1mm_Mask2mm"); f.SetFPID(pcbnew.LIB_ID("Fiducial", "Fiducial_1mm_Mask2mm"))
        f.SetReference(f"FID{i+1}"); f.SetAttributes(f.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        f.SetPosition(pcbnew.VECTOR2I(MM(OX + fx), MM(OY + fy))); f.Reference().SetVisible(False); f.SetLocked(True); b.Add(f)
    # fab layer: acrylic top plate cut line (0.5 mm inside the edge), connector cutouts, standoff zones
    def frect(x0, y0, x1, y1, layer=pcbnew.F_Fab, w=0.1):
        t = pcbnew.PCB_SHAPE(b); t.SetShape(pcbnew.SHAPE_T_RECT); t.SetLayer(layer); t.SetWidth(MM(w))
        t.SetStart(pcbnew.VECTOR2I(MM(OX + x0), MM(OY + y0))); t.SetEnd(pcbnew.VECTOR2I(MM(OX + x1), MM(OY + y1))); b.Add(t)
    def fcirc(cx, cy, r, layer=pcbnew.F_Fab, w=0.1):
        t = pcbnew.PCB_SHAPE(b); t.SetShape(pcbnew.SHAPE_T_CIRCLE); t.SetLayer(layer); t.SetWidth(MM(w))
        t.SetCenter(pcbnew.VECTOR2I(MM(OX + cx), MM(OY + cy))); t.SetEnd(pcbnew.VECTOR2I(MM(OX + cx + r), MM(OY + cy))); b.Add(t)
    frect(0.5, 0.5, W - 0.5, H - 0.5)
    if not LITE: frect(-0.5, 30.5 - 5.0, 9.5, 30.5 + 5.0)                                     # USB-C plate cutout
    if not LITE: frect(86.5, 30.5 - 7.5, W + 0.5, 30.5 + 7.5)                                # RCA plate cutout
    for ref in ("H1", "H2", "H3", "H4"):
        hx, hy, _ = P[ref]; fcirc(hx, hy, 3.5)                       # M3 standoff (6 mm hex) zone
    # net classes: power wider
    # JLC 2-layer standard capability (with margin): 0.127/0.127 min, 0.3 drill, 0.6 via, 0.3 copper-to-edge
    ds.m_TrackMinWidth = MM(0.127); ds.m_MinClearance = MM(0.127); ds.m_ViasMinSize = MM(0.6); ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3); ds.m_HoleClearance = MM(0.25); ds.m_HoleToHoleMin = MM(0.5); ds.m_ViasMinAnnularWidth = MM(0.13)
    ds.m_SilkClearance = MM(0.15); ds.SetBoardThickness(MM(1.6))
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass(); dflt.SetTrackWidth(MM(0.2)); dflt.SetClearance(MM(0.2)); dflt.SetViaDiameter(MM(0.6)); dflt.SetViaDrill(MM(0.3))
    pw = pcbnew.NETCLASS("Power"); pw.SetTrackWidth(MM(0.5)); pw.SetClearance(MM(0.2)); pw.SetViaDiameter(MM(0.6)); pw.SetViaDrill(MM(0.3))
    ns.SetNetclass("Power", pw)
    us = pcbnew.NETCLASS("USB_90R"); us.SetTrackWidth(MM(0.2)); us.SetClearance(MM(0.2)); us.SetViaDiameter(MM(0.6)); us.SetViaDrill(MM(0.3))
    us.SetDiffPairWidth(MM(0.2)); us.SetDiffPairGap(MM(0.15)); us.SetDiffPairViaGap(MM(0.3))
    ns.SetNetclass("USB_90R", us)
    for n in ("USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"):
        ns.SetNetclassPatternAssignment("/" + n, "USB_90R")
    for n in ("GND", "VBUS", "+5V_LOGIC", "+5V_CART", "+3V3", "+1V1"):
        ns.SetNetclassPatternAssignment("/" + n, "Power")
    for fp in b.GetFootprints():
        for pd in fp.Pads(): pd.SetTeardropsEnabled(True)
    tb = b.GetTitleBlock(); tb.SetTitle("LASAGNA LITE (WeAct RP2350B) Famicom cart interface" if LITE else "LASAGNA2354 Famicom cart interface"); tb.SetRevision("LITE" if LITE else "C"); tb.SetDate("2026-10-13")
    tb.SetCompany("Leo / Kobe")
    for i, cmt in enumerate(["2 layers, FR4 1.6 mm, 1 oz Cu, HASL lead-free", "Solder mask BLACK both sides, silkscreen WHITE",
                             "JLC standard 2-layer rules; see FAB_NOTES.md", "PROPOSAL - unrouted, not fab verified"]):
        tb.SetComment(i, cmt)
    for fp in b.GetFootprints():
        fp.Value().SetLayer(pcbnew.F_Fab)
        for fl in fp.GetFields():
            if fl.GetName() in ('LCSC', 'MPN'): fl.SetVisible(False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); fp.Reference().SetTextThickness(MM(0.12))
        fp.Reference().SetLayer(pcbnew.F_Fab)       # front silk carries only grid/title text (black mask: keep it clean)
    def txt(s, x, y, sz=1.0, layer=pcbnew.F_SilkS):
        t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer)
        t.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); t.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz))); t.SetTextThickness(MM(0.15)); t.SetMirrored(layer == pcbnew.B_SilkS); b.Add(t)
    def txt(s, x, y, sz=1.0, layer=pcbnew.F_SilkS, just=0, th=None, rot=0):
        t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer); t.SetTextAngleDegrees(rot)
        t.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); t.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz)))
        t.SetTextThickness(MM(th or sz * 0.15)); t.SetMirrored(layer == pcbnew.B_SilkS)
        if just: t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if just < 0 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        b.Add(t)
    G = 1.2                                          # single grid font size (coords, column numbers, CPU/PPU)
    for u in ICS:                                    # coordinate on the IC body (between pad rows)
        x, y, _ = P[u]; txt(COORD[u], x, y, G)
    for i, x in enumerate(COLS): txt(str(i + 1), x, IC_Y + 5.0, G)   # column numbers under row A
    txt("A", 2.5, IC_Y, G); txt("A", 97.5, IC_Y, G)                   # row letter on both edges
    # wordmark: three stacked "lasagna layer" bars + name + REV.C
    if LITE:
        # wordmark on the free front-left area (the module covers the centre): bars + LASAGNA LITE + SPAGHETTI COMPUTER
        LY0 = 26.4
        for k, wv in enumerate((4.0, 3.2, 4.0)):
            frect(4.6 - wv / 2, LY0 + k * 0.75, 4.6 + wv / 2, LY0 + k * 0.75 + 0.4, pcbnew.F_SilkS, 0.15)
        txt("LASAGNA", 7.2, LY0 + 1.0, 1.6, just=-1); txt("LITE", 18.0, LY0 + 1.25, 1.0, just=-1)
        txt("SPAGHETTI COMPUTER", 2.6, LY0 + 3.2, 0.8, just=-1, th=0.12)
        txt("CPU", 17.5, IC_Y + 5.0, G); txt("PPU", 82.5, IC_Y + 5.0, G)
        # module handling notes, front, right of H1 near GP23/GP0
        txt("WEACT RP2350B:", 71.2, 26.4, 0.8, just=-1, th=0.12)
        txt("LIFT R16 (GP23 KEY)", 71.2, 27.8, 0.8, just=-1, th=0.12)
        txt("NO PSRAM (GP0)", 71.2, 29.2, 0.8, just=-1, th=0.12)
        txt("CUT=USE D", 80.6, 59.9, 0.8, th=0.12); txt("BYP F", 74.6, 59.9, 0.8, th=0.12)
        for k, lb in enumerate(("SCL", "SDA", "3V3", "GND")): txt(lb, 5.0, 49.0 + 2.0 * k, 0.8, th=0.12)   # Grove J9 pins 1-4 (Seeed)
        txt("VIDEO", 98.0, 33.0, 1.0, rot=90); txt("AUDIO", 98.0, 49.0, 1.0, rot=90)
        txt("EXP", 21.7, 43.6, G, rot=90); txt("RST", 27.6, 41.3, G, rot=90); txt("PAD2", 9.5, 60.9, 0.8, th=0.12, rot=90); txt("PAD1", 9.5, 64.8, 0.8, th=0.12, rot=90)
    else:
        txt("CPU", COLS[1], 25.6, G); txt("PPU", COLS[5], 25.6, G)
        LY0 = 24.6
        for k, wv in enumerate((4.0, 3.2, 4.0)):
            frect(37.6 - wv / 2, LY0 + k * 0.75, 37.6 + wv / 2, LY0 + k * 0.75 + 0.4, pcbnew.F_SilkS, 0.15)
        txt("LASAGNA2354", 49.0, LY0 + 1.0, 1.6); txt("REV.C", 58.6, LY0 + 1.25, 0.9, just=-1)
        txt("USB", 11.0, 30.5, G, just=-1)
        txt("B2", P["U10"][0], P["U10"][1], G); txt("I2C", 11.5, 43.0, G, just=-1)
        txt("VIDEO", 98.6, 22.6, G, just=1); txt("CART", 92.6, 46.5, G, just=1)
        txt("PAD1", 9.5 + 3 * 2.54, FRONT_Y - 2.9, G); txt("PAD2", 90.5 - 3 * 2.54, FRONT_Y - 2.9, G)
        txt("SWD", 54.2, FRONT_Y + 2.5, G, just=-1); txt("RUN", 36, FRONT_Y - 4.0, G); txt("BOOT", 64, FRONT_Y - 4.0, G)
    # test points: THT, flipped to the back; signal-name labels on back silk only (none on the front)
    for i, (n, lbl) in enumerate(design.TPS):
        tp = F[f"TP{i+1}"]
        if tp.GetLayer() != pcbnew.B_Cu: tp.Flip(tp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)
        tp.Reference().SetLayer(pcbnew.B_Fab); tp.Reference().SetMirrored(True)
        if LITE: txt(lbl, P[f"TP{i+1}"][0], P[f"TP{i+1}"][1] + TP_LBL_DY, 0.8, pcbnew.B_SilkS, th=0.12)
        else: txt(lbl, P[f"TP{i+1}"][0], TP_LBL_Y, 1.0 if len(lbl) > 2 else G, pcbnew.B_SilkS, th=0.15)
    # back silk: minimal name/origin block, JLC order-number placeholder
    BX = 14.5 if LITE else 70.0                        # Lite: back of the free left area, clear of the module
    BY = 28.0 if LITE else 31.0
    txt("LASAGNA LITE" if LITE else "LASAGNA2354 REV.C", BX, BY, 1.2, pcbnew.B_SilkS, th=0.18)
    if LITE:   # company line + handling notes (back, mirrored like the rest of B.SilkS)
        txt("SPAGHETTI COMPUTER", BX, BY + 2.0, 0.9, pcbnew.B_SilkS, th=0.14)
        txt("MADE IN KOBE", BX, BY + 4.0, 1.0, pcbnew.B_SilkS, th=0.15)
        txt("JLCJLCJLCJLC", BX, BY + 6.0, 1.0, pcbnew.B_SilkS, th=0.12)
        txt("UNPLUG USB", BX, BY + 9.0, 1.0, pcbnew.B_SilkS, th=0.15)
        txt("BEFORE CART SWAP", BX, BY + 11.0, 1.0, pcbnew.B_SilkS, th=0.15)
        txt("LIFT MODULE R16 / NO PSRAM", BX, BY + 13.5, 0.8, pcbnew.B_SilkS, th=0.12)
    else:
        txt("MADE IN KOBE", BX, 33.0, 1.0, pcbnew.B_SilkS, th=0.15)
        txt("JLCJLCJLCJLC", BX, 35.0, 0.8, pcbnew.B_SilkS, th=0.12)
    b.Save(str(OUTD / f"{NAME}.kicad_pcb"))
    print("footprints", len(b.GetFootprints()), "nets", len(nets))

if __name__ == "__main__":
    main()

STACKUP = '''(stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "HAL lead-free")
      (dielectric_constraints no)
    )
    '''
def add_stackup():
    p = OUTD / f"{NAME}.kicad_pcb"; t = p.read_text()
    if "(stackup" not in t:
        t = t.replace("(setup", "(setup\n    " + STACKUP, 1); p.write_text(t)
add_stackup()

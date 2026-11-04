#!/usr/bin/env python3
"""LASAGNA LITE schematic: hierarchical, drawn (wires/junctions/power symbols), A3 sheets.

Used by gen_sch.py only when LASAGNA_LITE=1 (Rev.C keeps its flat label-per-pin sheet).
Net naming is kept identical to the flat sheet ("/NET"): every non-power net in a
sub-sheet is a hierarchical label that is brought up to a local label on the root
sheet, and the power symbols carry the value "/GND", "/+5V_LOGIC", "/+3V3" (the
visible text is the plain rail name), so the PCB footprint nets do not change.
"""
import math
import design
from gen_sch import (OUT, NAME, LIB, ROOT, U, q, f, STEP, sym_geometry, FLAG_PINS)

PAPER = "A3"
import os
# KiCad 9.0.2 has no sheet-local power symbols and escapes "/" in a power value ("{slash}GND"),
# so real power symbols would rename the rails to GND/+5V_LOGIC/+3V3 (PCB uses "/GND" etc.).
# Default: rails are hierarchical labels -> root labels (net names unchanged).
PWR_SYMBOLS = os.environ.get("LASAGNA_LITE_PWRSYM") == "1"
POWER = {"GND": "GND", "+5V_LOGIC": "+5V_LOGIC", "+3V3": "+3V3"}
STUB = 2.54
CH = 1.27 * 0.95          # approx label char width (font 1.27)

def g(v):                  # snap to 1.27 grid
    return round(v / 1.27) * 1.27

def geometry(pins):
    if len(pins) == 1:
        return [(pins[0], -5.08, 0.0, 0)], 2.54, 1.27
    return sym_geometry(pins)

def lib_symbol(name, pins, inbom=True):
    geo, hw, hh = geometry(pins)
    inner = []
    for (num, pname, ptype), x, y, ang in geo:
        inner.append(f'(pin {ptype} line (at {f(x)} {f(y)} {ang}) (length 2.54) (name {q(pname)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))')
    b = "yes" if inbom else "no"
    pn = "(pin_names (offset 0.5))" if len(pins) > 2 else "(pin_names (offset 0.5) hide)"
    return f'''(symbol {q(LIB + ":" + name)} {pn} (exclude_from_sim no) (in_bom {b}) (on_board {b})
  (property "Reference" "U" (at 0 {f(hh + 2.54)} 0) (effects (font (size 1.27 1.27))))
  (property "Value" {q(name)} (at 0 {f(-hh - 2.54)} 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol {q(name + "_0_1")} (rectangle (start {f(-hw)} {f(hh)}) (end {f(hw)} {f(-hh)}) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol {q(name + "_1_1")} {" ".join(inner)}))'''

def power_symbol(net):
    """Global power symbol, graphic points 'down' (-y) from the pin at origin."""
    name = "PWR_" + net.replace("+", "P")
    if net == "GND":
        gr = '(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))'
    else:
        gr = '(polyline (pts (xy 0 0) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))'
    return name, f'''(symbol {q(LIB + ":" + name)} (power) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom no) (on_board no)
  (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" {q("/" + net)} (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol {q(name + "_0_1")} {gr})
  (symbol {q(name + "_1_1")} (pin power_in line (at 0 0 270) (length 0) hide (name {q("/" + net)} (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))))'''

DIRS = {(-1, 0): "L", (1, 0): "R", (0, -1): "U", (0, 1): "D"}

def rot(x, y, r):
    a = math.radians(r)
    return (round(x * math.cos(a) - y * math.sin(a), 4), round(x * math.sin(a) + y * math.cos(a), 4))

def P(x, y):
    return (round(x, 3), round(y, 3))

class Sheet:
    def __init__(s, key, title, page, paper="A4"):
        s.key, s.title, s.page, s.paper = key, title, page, paper
        s.file = f"{NAME}_{key}.kicad_sch"
        s.uuid = U("lite-sheet", key)
        s.body, s.segs, s.pins, s.pwr_pts = [], [], {}, []
        s.done = set(); s.nets = set(); s.refs = []; s.npwr = 0; s.blocks = []
        s.bbox_pts = {}; s.pwrnets = set(); s.owner = None

    # ---- components
    def place(s, ref, x, y, r=0, textpos=None):
        c = COMP[ref]; s.refs.append(ref)
        geo, hw, hh = geometry(c["pins"])
        cx, cy = g(x), g(y)
        pts = []
        for (num, pname, ptype), px, py, ang in geo:
            ox, oy = {0: (-1, 0), 180: (1, 0), 90: (0, -1), 270: (0, 1)}[ang]
            rx, ry = rot(px, py, r); dx, dy = rot(ox, oy, r)
            end = P(cx + rx, cy - ry); d = (int(round(dx)), int(-round(dy)))
            s.pins[(ref, num)] = (end, d, c["nets"].get(num))
            pts.append(end)
        # body corners
        for bx, by in [(-hw, hh), (hw, -hh)]:
            rx, ry = rot(bx, by, r); pts.append(P(cx + rx, cy - ry))
        s.bbox_pts[ref] = pts
        isflag = ref.startswith("#FLG")
        inb = "no" if isflag else "yes"
        vertical = r in (90, 270)
        if textpos is None:
            textpos = "side" if vertical else "tb"
        if textpos == "side":
            ext = (hh if vertical else hw) + 1.27
            rp, vp, j = (cx + ext, cy - 1.27), (cx + ext, cy + 1.27), "left"
        else:
            ext = (hw if vertical else hh)
            rp, vp, j = (cx, cy - ext - 1.27), (cx, cy + ext + 1.27), None
        props = [("Reference", c["ref"], rp, False, j, "bottom"), ("Value", c["value"], vp, False, j, "top"),
                 ("Footprint", c["fp"], (cx, cy), True, None, None), ("Datasheet", "", (cx, cy), True, None, None)]
        if not isflag:
            lc = design.LCSC.get(c["mpn"])
            props += [("MPN", c["mpn"], (cx, cy), True, None, None), ("LCSC", lc[0] if lc else "", (cx, cy), True, None, None),
                      ("LCSC_Status", lc[1] if lc else ("hand-assembly / not PCBA" if c["dnp"] else "no LCSC part"), (cx, cy), True, None, None),
                      ("Note", c["note"], (cx, cy), True, None, None)]
        def eff(hide, j, v):
            js = []
            if j: js.append(j)
            if v and j: js.append(v)
            jt = f' (justify {" ".join(js)})' if js else ""
            return f'(effects (font (size 1.27 1.27)){jt}{" hide" if hide else ""})'
        fa = (360 - r) % 360 if vertical else 0
        ptxt = " ".join(f'(property {q(k)} {q(v)} (at {f(p[0])} {f(p[1])} {fa}) {eff(h, j, vj)})' for k, v, p, h, j, vj in props)
        pin_uuids = " ".join(f'(pin {q(p[0])} (uuid {q(U(c["ref"], "pin", p[0]))}))' for p in c["pins"])
        dnp = "yes" if c["dnp"] else "no"
        s.body.append(f'''(symbol (lib_id {q(LIB + ":" + c["sym"])}) (at {f(cx)} {f(cy)} {r}) (unit 1) (exclude_from_sim no) (in_bom {inb}) (on_board {inb}) (dnp {dnp}) (uuid {q(U(c["ref"]))})
  {ptxt} {pin_uuids}
  (instances (project {q(NAME)} (path {q("/" + ROOT + "/" + s.uuid)} (reference {q(c["ref"])}) (unit 1)))))''')
        return s

    def pin(s, rp):
        ref, num = rp.split(".")
        return s.pins[(ref, num)]

    # ---- wiring primitives
    def wire(s, *pts):
        pts = [P(*p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a == b: continue
            assert a[0] == b[0] or a[1] == b[1], (s.key, a, b)
            seg = tuple(sorted([a, b]))
            if seg not in s.segs: s.segs.append(seg)

    def route(s, a, b, mid=None):
        """Orthogonal wire pin a -> pin b through each pin's stub end."""
        (ea, da, na), (eb, db, nb) = s.pin(a), s.pin(b)
        assert na == nb, (a, b, na, nb)
        ca = P(ea[0] + da[0] * STUB, ea[1] + da[1] * STUB)
        cb = P(eb[0] + db[0] * STUB, eb[1] + db[1] * STUB)
        if mid is not None:                           # vertical jog at x=mid (or horizontal at y=mid)
            if da[1] == 0: path = [ca, (mid, ca[1]), (mid, cb[1]), cb]
            else: path = [ca, (ca[0], mid), (cb[0], mid), cb]
        elif ca[0] == cb[0] or ca[1] == cb[1]: path = [ca, cb]
        elif da[1] == 0: path = [ca, (cb[0], ca[1]), cb]
        else: path = [ca, (ca[0], cb[1]), cb]
        s.wire(ea, *path, eb)
        s.done |= {a, b}
        return ca, cb

    def stub_end(s, rp, n=1):
        e, d, _ = s.pin(rp)
        return P(e[0] + d[0] * STUB * n, e[1] + d[1] * STUB * n)

    def label(s, net, pt, d):
        """Hierarchical label (sub-sheet) at pt, pointing along d (away from the wire)."""
        s.nets.add(net)
        ang, just = {"L": (180, "right"), "R": (0, "left"), "U": (90, "left"), "D": (270, "right")}[d]
        s.body.append(f'(hierarchical_label {q(net)} (shape passive) (at {f(pt[0])} {f(pt[1])} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(U(s.key, "hl", net, pt))}))')
        k = s.owner or (s.refs[-1] if s.refs else "_lbl")
        s.bbox_pts.setdefault(k, []).append(pt)
        L = len(net) * CH + 3
        v = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}[d]
        s.bbox_pts[k].append(P(pt[0] + v[0] * L, pt[1] + v[1] * L))

    def power(s, net, pt, d):
        """Power symbol whose graphic points along d from pt."""
        name = "PWR_" + net.replace("+", "P")
        r = {"D": 0, "R": 90, "L": 270, "U": 180}[d]
        s.npwr += 1
        ref = f"#PWR_{s.key}_{s.npwr:03d}"
        s.body.append(f'''(symbol (lib_id {q(LIB + ":" + name)}) (at {f(pt[0])} {f(pt[1])} {r}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid {q(U(s.key, "pwr", s.npwr))})
  (property "Reference" {q(ref)} (at {f(pt[0])} {f(pt[1])} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" {q("/" + net)} (at {f(pt[0])} {f(pt[1])} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Footprint" "" (at {f(pt[0])} {f(pt[1])} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at {f(pt[0])} {f(pt[1])} 0) (effects (font (size 1.27 1.27)) hide))
  (pin "1" (uuid {q(U(s.key, "pwrpin", s.npwr))}))
  (instances (project {q(NAME)} (path {q("/" + ROOT + "/" + s.uuid)} (reference {q(ref)}) (unit 1)))))''')
        s.pwr_pts.append(P(*pt)); s.pwrnets.add(net)

    def term(s, net, pt, d):
        if net in POWER and PWR_SYMBOLS: s.power(net, pt, d)
        else: s.label(net, pt, d)

    def tap(s, pt, d, net, n=1):
        v = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}[d]
        e = P(pt[0] + v[0] * STUB * n, pt[1] + v[1] * STUB * n)
        s.wire(pt, e); s.term(net, e, d)
        return e

    def block(s, title, refs, pad=3.81):
        s.blocks.append((title, refs, pad))

    # ---- finish
    def finish(s):
        # default: stub + label / power symbol / no-connect for every unhandled pin
        for (ref, num), (e, d, net) in s.pins.items():
            if f"{ref}.{num}" in s.done: continue
            if net is None:
                s.body.append(f'(no_connect (at {f(e[0])} {f(e[1])}) (uuid {q(U(s.key, "nc", ref, num))}))')
                continue
            pe = P(e[0] + d[0] * STUB, e[1] + d[1] * STUB)
            s.wire(e, pe)
            s.owner = ref; s.term(net, pe, "R" if d[0] == 0 else DIRS[d]); s.owner = None
            s.bbox_pts.setdefault(ref, []).append(pe)
            if net not in POWER or not PWR_SYMBOLS:
                L = len(net) * CH + 3
                dd = (1, 0) if d[0] == 0 else d
                s.bbox_pts[ref].append(P(pe[0] + dd[0] * L, pe[1] + dd[1] * L + (1.5 if d[0] == 0 else 0)))
            else:
                s.bbox_pts[ref].append(P(pe[0] + d[0] * 5, pe[1] + d[1] * 5))
        for rp in s.done:
            ref, num = rp.split(".")
            net = s.pins[(ref, num)][2]
            assert net in POWER or net in s.nets or net in s.pwrnets, (s.key, "routed net without label", rp, net)
        # sanity: no wire may pass through a foreign pin end / over another wire's end unintentionally
        pinends = {}
        for (ref, num), (e, d, net) in s.pins.items(): pinends.setdefault(e, []).append((ref, num))
        def on_interior(p, seg):
            (x1, y1), (x2, y2) = seg
            if x1 == x2 == p[0]: return min(y1, y2) < p[1] < max(y1, y2)
            if y1 == y2 == p[1]: return min(x1, x2) < p[0] < max(x1, x2)
            return False
        for p, who in pinends.items():
            for seg in s.segs:
                assert not on_interior(p, seg), (s.key, "wire crosses pin", who, seg)
        # collinear overlaps
        for i, a in enumerate(s.segs):
            for b in s.segs[i + 1:]:
                if a[0][0] == a[1][0] == b[0][0] == b[1][0]:
                    lo, hi = max(min(a[0][1], a[1][1]), min(b[0][1], b[1][1])), min(max(a[0][1], a[1][1]), max(b[0][1], b[1][1]))
                    assert hi <= lo, (s.key, "overlap", a, b)
                if a[0][1] == a[1][1] == b[0][1] == b[1][1]:
                    lo, hi = max(min(a[0][0], a[1][0]), min(b[0][0], b[1][0])), min(max(a[0][0], a[1][0]), max(b[0][0], b[1][0]))
                    assert hi <= lo, (s.key, "overlap", a, b)
        # split wires at T points (KiCad only connects wire end points)
        changed = True
        while changed:
            changed = False
            ends = {p for seg in s.segs for p in seg}
            for seg in list(s.segs):
                for p in ends:
                    if on_interior(p, seg):
                        s.segs.remove(seg); s.segs += [tuple(sorted([seg[0], p])), tuple(sorted([p, seg[1]]))]
                        changed = True; break
                if changed: break
        # junctions
        pts = {}
        for seg in s.segs:
            for p in seg: pts[p] = pts.get(p, 0) + 1
        juncs = []
        for p, n in pts.items():
            n += sum(2 for seg in s.segs if on_interior(p, seg))
            n += len(pinends.get(p, [])) + s.pwr_pts.count(p)
            if n >= 3: juncs.append(p)
        for seg in s.segs:
            s.body.append(f'(wire (pts (xy {f(seg[0][0])} {f(seg[0][1])}) (xy {f(seg[1][0])} {f(seg[1][1])})) (stroke (width 0) (type default)) (uuid {q(U(s.key, "w", seg))}))')
        for p in juncs:
            s.body.append(f'(junction (at {f(p[0])} {f(p[1])}) (diameter 0) (color 0 0 0 0) (uuid {q(U(s.key, "j", p))}))')
        s.njunc = len(juncs)
        # block frames
        for title, refs, pad in s.blocks:
            xs, ys = [], []
            for r in refs:
                for p in s.bbox_pts.get(r, []): xs.append(p[0]); ys.append(p[1])
            x0, y0, x1, y1 = g(min(xs) - pad), g(min(ys) - pad - 5.08), g(max(xs) + pad), g(max(ys) + pad)
            x1 = max(x1, g(x0 + len(title) * 1.9 + 3))
            s.body.append(f'(rectangle (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.254) (type dash) (color 0 0 194 1)) (fill (type none)) (uuid {q(U(s.key, "box", title))}))')
            s.body.append(f'(text {q(title)} (exclude_from_sim no) (at {f(x0 + 1.27)} {f(y0 + 1.27)} 0) (effects (font (size 2 2) (thickness 0.4) bold (color 0 0 194 1)) (justify left top)) (uuid {q(U(s.key, "boxt", title))}))')
            s.frame = (x0, y0, x1, y1)

    def text(s, x, y, t, size=1.5):
        s.body.append(f'(text {q(t).replace(chr(10), "\\n")} (exclude_from_sim no) (at {f(x)} {f(y)} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {q(U(s.key, "txt", t))}))')

    def write(s, lib_syms):
        txt = f'''(kicad_sch (version 20231120) (generator "nespico_gen") (generator_version "9.0") (uuid {q(s.uuid)}) (paper {q(s.paper)})
  (title_block (title {q("LASAGNA LITE - " + s.title)}) (date "2026-10-17") (rev "Lite-WeAct-draft2") (comment 1 "Not reviewed; not a fabrication sign-off") (comment 2 "Generated by gen_sch.py (LASAGNA_LITE=1) from design.py"))
  (lib_symbols {lib_syms})
  {chr(10).join(s.body)}
)
'''
        (OUT / s.file).write_text(txt)

COMP = {}

# --------------------------------------------------------------------------- layouts
def L_power(s):
    # WeAct module: USB-C, CC resistors and ESD are on the module; VBUS_IN = module H1-1 (raw USB VBUS, sheet "WeAct module")
    # power path: VBUS_IN -F1/JP2- VBUS_F -D2/JP1- +5V_LOGIC
    y = 48.26
    s.place("F1", 60.96, y).place("JP2", 60.96, y + 12.7)
    s.place("D2", 106.68, y, 180).place("JP1", 106.68, y + 12.7)
    s.route("F1.1", "JP2.1"); s.route("F1.2", "JP2.2")
    s.route("F1.2", "D2.2"); s.route("D2.2", "JP1.1")
    s.route("D2.1", "JP1.2")
    s.tap(s.stub_end("F1.1"), "L", "VBUS_IN")
    a, b = s.stub_end("F1.2"), s.stub_end("D2.2")
    s.tap(P(g((a[0] + b[0]) / 2), y), "U", "VBUS_F")
    ca = s.stub_end("D2.1")
    s.place("C1", ca[0] + 10.16, y + 7.62, 270)
    s.route("D2.1", "C1.1")
    s.place("TP2", ca[0] + 30.48, y)
    s.route("C1.1", "TP2.1")
    s.tap(s.stub_end("C1.1"), "U", "+5V_LOGIC")
    s.block("Power path: F1 PTC (JP2 bypass) -> D2 SS34 (JP1 bypass)", ["F1", "JP2", "D2", "JP1", "C1", "TP2"])
    flg = [k for k in COMP if k.startswith("#FLG")]
    for i, r in enumerate(flg):
        s.place(r, 60.96 + i * 30.48, 95)
    s.place("TP1", 60.96, 110).place("TP11", 91.44, 110).place("TP22", 121.92, 110)
    for i, r in enumerate(["H1", "H2", "H3", "H4"]):
        s.place(r, 66.04 + i * 12.7, 125, 270)
    for a, b in zip(["H1", "H2", "H3"], ["H2", "H3", "H4"]):
        s.route(a + ".1", b + ".1")
    s.tap(s.stub_end("H1.1"), "L", "GND")
    s.block("Power flags, rail test points, mounting holes", flg + ["TP1", "TP11", "TP22", "H1", "H2", "H3", "H4"])
    s.text(20, 160, "VBUS_IN = WeAct H1-1 (raw USB VBUS, before the module's diode U2). F1 = 500 mA PTC (JP2 shorts it),\n"
                    "D2 = SS34 (DNP, JP1 bridged) -> +5V_LOGIC. H1-2 (+5V after the diode) is NOT used: the drop could take the AHCT below 4.5 V.\n"
                    "+3V3 comes from the module LDO (H2-5/H2-6, sheet 'WeAct module'). H2-3 3V3_EN, H1-5 VREF and H2-8 RUN stay unconnected.")

def L_core(s):
    s.place("U1", 95, 100)
    s.block("WeAct Studio RP2350B Core Board V1.0 (H1 + H2, 2x15 each)", ["U1"])
    s.place("C27", 200, 50, 270)
    s.block("3V3 bypass (U10)", ["C27"])
    s.text(175, 80, "Pins 101-130 = H1 pin 1-30, 201-230 = H2 pin 1-30.\n"
                    "PPU on GP0-17, IRQ/CIRAM/OE#/CVBS on GP18-24,\nCPU on GP25-43, I2C 44/45, audio 46, spare 47.\n"
                    "GP40-47 (ADC, NOT 5V tolerant): AHCT inputs / 3V3 parts only.\n"
                    "Module: LIFT R16 (GP23 KEY), never fit PSRAM U7 (CS = GP0).\nGP25 drives the module LED via 5.1k.")

def decaps(s, refs, x, y):
    for i, r in enumerate(refs):
        s.place(r, x + i * 12.7, y, 270)
    for a, b in zip(refs, refs[1:]):
        s.route(a + ".1", b + ".1"); s.route(a + ".2", b + ".2")
    s.tap(s.stub_end(refs[0] + ".1"), "L", "+5V_LOGIC")
    s.tap(s.stub_end(refs[0] + ".2"), "L", "GND")

def bus_sheet(s, rns, latch, buf, caps, tps, names, pull=None):
    s.place(rns[0], 45, 45).place(rns[1], 45, 75)
    s.block(names[0], rns)
    s.place(latch, 135, 55)
    s.block(names[1], [latch])
    s.place(buf, 135, 125)
    s.block(names[2], [buf])
    decaps(s, caps, 225, 45)
    s.block("Decoupling " + "/".join([latch, buf]), caps)
    y = 80
    if pull:
        s.place(pull, 230, 78, 90); s.block("/OE pull-up", [pull]); y = 108
    for i, r in enumerate(tps):
        s.place(r, 232, y + i * 10.16)
    s.block("Test points", tps)

def L_cpu(s):
    bus_sheet(s, ["RN1", "RN2"], "U2", "U6", ["C10", "C14"], ["TP3", "TP8", "TP10"],
              ["33R series (module -> CPU AD bus)", "CPU A0-A7 latch (74AHCT573)", "CPU A8-A14, R/W buffer (74AHCT541)"], pull="R30")

def L_ppu(s):
    bus_sheet(s, ["RN3", "RN4"], "U3", "U7", ["C11", "C15"], ["TP17", "TP21"],
              ["33R series (module -> PPU AD bus)", "PPU A0-A7 latch (74AHCT573)", "PPU A8-A13, /ROMSEL, /WR buffer (74AHCT541)"])

def L_xcvr(s):
    s.place("U4", 50, 55)
    s.block("CPU data transceiver (74AHCT245)", ["U4"])
    s.place("U5", 140, 55)
    s.block("PPU data transceiver (74AHCT245)", ["U5"])
    s.place("U8", 50, 130)
    s.block("Control decoder / inverter (74AHCT540)", ["U8"])
    decaps(s, ["C12", "C13", "C16"], 222, 45)
    s.block("Decoupling U4/U5/U8", ["C12", "C13", "C16"])
    s.place("R31", 225, 82, 90).place("R32", 250, 82, 90)
    s.block("Enable pull-ups", ["R31", "R32"])
    for i, r in enumerate(["TP4", "TP16", "TP18", "TP19", "TP20"]):
        s.place(r, 140, 110 + i * 10.16)
    s.block("Test points", ["TP4", "TP16", "TP18", "TP19", "TP20"])

def L_cart(s):
    s.place("J3", 85, 100)
    s.block("Famicom 60-pin cartridge slot (J3)", ["J3"])
    s.place("R39", 185, 50, 90).place("R41", 215, 50, 270)
    s.block("IRQ pull-up / CIRAM_A10 pull-down", ["R39", "R41"])
    for i, r in enumerate(["TP5", "TP6", "TP7", "TP9", "TP14", "TP15"]):
        s.place(r, 190, 85 + i * 10.16)
    s.block("Cart test points", ["TP5", "TP6", "TP7", "TP9", "TP14", "TP15"])

def L_opt(s):
    # MCP23017 + pads
    s.place("U10", 70, 80)
    s.place("R51", 125, 50, 90).place("R52", 140, 50, 90).place("R53", 155, 50, 90)
    s.block("Controller-port expander MCP23017 (DNP) + I2C pull-ups", ["U10", "R51", "R52", "R53"])
    s.place("J4", 70, 140).place("J5", 70, 175)
    s.place("R42", 125, 140, 90).place("R43", 140, 140, 90)
    s.block("Controller pads J4/J5 (DNP) + data pull-ups", ["J4", "J5", "R42", "R43"])
    s.place("J9", 70, 215)
    s.block("Grove I2C (HY2.0-4P)", ["J9"])
    # CVBS DAC
    x, y = 205, 50.8
    s.place("R90", x, y).place("R91", x, y + 7.62).place("R92", x, y + 15.24)
    s.route("R90.2", "R91.2"); s.route("R91.2", "R92.2")
    s.place("J6", x + 25.4, y, 0)
    s.route("R90.2", "J6.1")
    a, b = s.stub_end("R90.2"), s.stub_end("J6.1")
    s.tap(P(g((a[0] + b[0]) / 2), a[1]), "U", "CVBS")
    s.block("CVBS 3-bit resistor DAC -> RCA (DNP)", ["R90", "R91", "R92", "J6"])
    # audio
    x, y = 205, 120.65
    s.place("R60", x, y)
    n = s.stub_end("R60.2")
    s.place("C60", n[0], y + 7.62, 270)
    s.place("C61", n[0] + 15.24, y)
    s.route("R60.2", "C61.1"); s.route("R60.2", "C60.1")
    m = s.stub_end("C61.2")
    s.place("R61", m[0], y + 7.62, 270)
    s.place("J11", m[0] + 15.24, y)
    s.route("C61.2", "J11.1"); s.route("C61.2", "R61.1")
    s.place("R62", x, y - 12.7)
    s.route("R62.2", "R60.2")
    a, b = s.stub_end("R60.2"), s.stub_end("C61.1")
    s.tap(P(g((a[0] + b[0]) / 2), a[1]), "U", "AUD_F")
    a, b = s.stub_end("C61.2"), s.stub_end("J11.1")
    s.tap(P(g((a[0] + b[0]) / 2), a[1]), "U", "AUD_OUT")
    s.block("Audio out: GP46 PWM -> RC -> RCA, cart pin 46 mix (DNP)", ["R60", "C60", "C61", "R61", "J11", "R62"])
    s.place("J10", 220, 185)
    s.place("TP12", 220, 215).place("TP13", 250, 215)
    s.place("J12", 280, 185)
    s.block("EXP header, external RESET (J12), spare GPIO test points", ["J10", "J12", "TP12", "TP13"])

SHEETS = [("power", "Power", L_power), ("core", "WeAct module", L_core),
          ("cpu", "CPU address latch & bus", L_cpu), ("ppu", "PPU address latch & bus", L_ppu),
          ("xcvr", "Data transceivers & decoder", L_xcvr), ("cart", "Cartridge slot", L_cart),
          ("options", "Options (pads, Grove, CVBS, audio, EXP)", L_opt)]

def main():
    used = {n for c in design.COMPS for n in c["nets"].values()}
    flags = [n for n in ["GND", "VBUS", "+5V_LOGIC", "+5V_CART", "+1V1", "VREG_AVDD"] if n in used]
    for c in design.COMPS: COMP[c["ref"]] = c
    for i, n in enumerate(flags):
        COMP[f"#FLG{i}"] = dict(ref=f"#FLG{i}", sym="PWRFLAG", pins=FLAG_PINS, nets={"1": n}, value="PWR_FLAG", fp="", mpn="", dnp=False, note="")
    syms = {}
    for c in design.COMPS: syms.setdefault(c["sym"], c["pins"])
    lib_forms = {n: lib_symbol(n, p) for n, p in syms.items()}
    lib_forms["PWRFLAG"] = lib_symbol("PWRFLAG", FLAG_PINS, inbom=False)
    for n in POWER:
        k, v = power_symbol(n); lib_forms[k] = v
    (OUT / f"{LIB}.kicad_sym").write_text("(kicad_symbol_lib (version 20231120) (generator nespico_gen)\n" +
        "\n".join(x.replace(f'(symbol "{LIB}:', '(symbol "', 1) for x in lib_forms.values()) + "\n)\n")
    (OUT / "sym-lib-table").write_text(f'(sym_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr ""))\n)\n')
    allsyms = " ".join(lib_forms.values())
    sheets = []
    for i, (key, title, fn) in enumerate(SHEETS):
        s = Sheet(key, title, i + 2, "A3" if key == "options" else "A4"); fn(s); s.finish(); s.write(allsyms); sheets.append(s)
    placed = [r for s in sheets for r in s.refs]
    assert sorted(placed) == sorted(COMP), (set(COMP) - set(placed), [r for r in placed if placed.count(r) > 1])
    # ---- root: block diagram with sheet symbols, every sheet port -> local label
    body = []
    pos = [(30, 35), (130, 35), (230, 35), (330, 35), (30, 165), (130, 165), (230, 165)]
    W = 30.48
    for s, (x, y) in zip(sheets, pos):
        ports = sorted(s.nets)
        rows = (len(ports) + 1) // 2
        x, y = g(x + 20), g(y)
        H = g(rows * 2.54 + 5.08)
        pins = []
        for k, net in enumerate(ports):
            left = k < rows
            py = y + 3.81 + (k if left else k - rows) * 2.54
            px = x if left else x + W
            pins.append(f'(pin {q(net)} passive (at {f(px)} {f(py)} {180 if left else 0}) (uuid {q(U("root", s.key, net))}) (effects (font (size 1.27 1.27)) (justify {"left" if left else "right"})))')
            ex = px - STUB if left else px + STUB
            body.append(f'(wire (pts (xy {f(px)} {f(py)}) (xy {f(ex)} {f(py)})) (stroke (width 0) (type default)) (uuid {q(U("root", "w", s.key, net))}))')
            body.append(f'(label {q(net)} (at {f(ex)} {f(py)} {180 if left else 0}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {"right" if left else "left"} bottom)) (uuid {q(U("root", "l", s.key, net))}))')
        body.append(f'''(sheet (at {f(x)} {f(y)}) (size {f(W)} {f(H)}) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 255 255 225 1.0000)) (uuid {q(s.uuid)})
  (property "Sheetname" {q(s.title.split(":")[0])} (at {f(x)} {f(y - 0.71)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
  (property "Sheetfile" {q(s.file)} (at {f(x)} {f(y + H + 0.59)} 0) (effects (font (size 1.27 1.27)) (justify left top)))
  {" ".join(pins)}
  (instances (project {q(NAME)} (path {q("/" + ROOT)} (page {q(str(s.page))})))))''')
    note = ("LASAGNA LITE: WeAct Studio RP2350B Core Board + Rev.C cart circuit (dump-oriented, hand-solder). PROPOSAL, NOT REVIEWED. "
            "Generated with LASAGNA_LITE=1 by ../revc/gen_sch.py from ../revc/design.py.\n"
            "Top level: one sheet per functional block; "
            "labels with the same name are the same net. Unverified: Famicom slot footprint/mechanics, RCA footprint, timing. See README.md.")
    body.append(f'(text {q(note).replace(chr(10), "\\n")} (exclude_from_sim no) (at 20 20 0) (effects (font (size 1.6 1.6)) (justify left bottom)) (uuid {q(U("note"))}))')
    sch = f'''(kicad_sch (version 20231120) (generator "nespico_gen") (generator_version "9.0") (uuid {q(ROOT)}) (paper {q(PAPER)})
  (title_block (title "LASAGNA LITE (WeAct RP2350B) board (proposal) - top level") (date "2026-10-17") (rev "Lite-WeAct-draft2") (comment 1 "Not reviewed; not a fabrication sign-off"))
  (lib_symbols)
  {chr(10).join(body)}
  (sheet_instances (path "/" (page "1")))
)
'''
    (OUT / f"{NAME}.kicad_sch").write_text(sch)
    print("components", len(design.COMPS), "sheets", len(sheets),
          "wires", sum(len(s.segs) for s in sheets), "junctions", sum(s.njunc for s in sheets))

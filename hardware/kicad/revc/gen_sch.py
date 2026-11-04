#!/usr/bin/env python3
"""Generate LASAGNA2354_RevC.kicad_sch (label-per-pin functional schematic) + symbol lib."""
import uuid
from pathlib import Path
import design

HERE = Path(__file__).parent
OUT, NAME = (HERE.parent / "revc_lite", "LASAGNA2354_Lite") if design.LITE else (HERE, "LASAGNA2354_RevC")
OUT.mkdir(exist_ok=True)
LIB = "NESPICO_RevC"
ROOT = str(uuid.uuid5(uuid.NAMESPACE_DNS, "nespico-revc-root"))
U = lambda *k: str(uuid.uuid5(uuid.NAMESPACE_DNS, "/".join(map(str, k))))
q = lambda s: '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
STEP = 2.54

def sym_geometry(pins):
    n = len(pins)
    if n == 2:
        return [(p, -5.08 if i == 0 else 5.08, 0.0, 0 if i == 0 else 180) for i, p in enumerate(pins)], 2.54, 1.27
    left = pins[: (n + 1) // 2]; right = pins[(n + 1) // 2:]
    rows = max(len(left), len(right))
    top = (rows - 1) * STEP / 2
    top = round(top / STEP) * STEP
    out = []
    for i, p in enumerate(left): out.append((p, -12.7, top - i * STEP, 0))
    for i, p in enumerate(right): out.append((p, 12.7, top - i * STEP, 180))
    return out, 10.16, rows * STEP / 2 + 1.27

def lib_symbol(name, pins, flag=False, inbom=True):
    geo, hw, hh = sym_geometry(pins)
    inner = []
    for (num, pname, ptype), x, y, ang in geo:
        inner.append(f'(pin {ptype} line (at {f(x)} {f(y)} {ang}) (length 2.54) (name {q(pname)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))')
    b = "yes" if inbom else "no"
    return f'''(symbol {q(LIB + ":" + name if not flag else name)} (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom {b}) (on_board {b})
  (property "Reference" "U" (at 0 {f(hh + 2.54)} 0) (effects (font (size 1.27 1.27))))
  (property "Value" {q(name)} (at 0 {f(-hh - 2.54)} 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol {q(name + "_0_1")} (rectangle (start {f(-hw)} {f(hh)}) (end {f(hw)} {f(-hh)}) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol {q(name + "_1_1")} {" ".join(inner)}))'''

FLAG_PINS = [("1", "PWR", "power_out")]

def main():
    syms = {}
    for c in design.COMPS:
        syms.setdefault(c["sym"], c["pins"])
    lib_forms = {n: lib_symbol(n, p) for n, p in syms.items()}
    lib_forms["PWRFLAG"] = lib_symbol("PWRFLAG", FLAG_PINS, inbom=False)
    (OUT / f"{LIB}.kicad_sym").write_text("(kicad_symbol_lib (version 20231120) (generator nespico_gen)\n" +
        "\n".join(x.replace(f'(symbol "{LIB}:', '(symbol "', 1) for x in lib_forms.values()) + "\n)\n")
    (OUT / "sym-lib-table").write_text(f'(sym_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr ""))\n)\n')
    body = []
    # layout in columns
    x, y, colw, maxy = 25.4, 25.4, 60.96, 560
    used = {n for c in design.COMPS for n in c["nets"].values()}
    flags = [n for n in ["GND", "VBUS", "+5V_LOGIC", "+5V_CART", "+1V1", "VREG_AVDD"] if n in used]
    items = [(c, False) for c in design.COMPS] + [(dict(ref=f"#FLG{i}", sym="PWRFLAG", pins=FLAG_PINS, nets={"1": n}, value="PWR_FLAG", fp="", mpn="", dnp=False, note=""), True) for i, n in enumerate(flags)]
    for c, isflag in items:
        geo, hw, hh = sym_geometry(c["pins"])
        h = 2 * hh + 12.7
        if y + h > maxy:
            x += colw; y = 25.4
        cx = round(x / STEP) * STEP; cy = round((y + hh + 5.08) / STEP) * STEP
        y += h
        lib_id = LIB + ":" + c["sym"]
        inb = "no" if isflag else "yes"
        props = [("Reference", c["ref"], hh + 2.54, False), ("Value", c["value"], -hh - 2.54, False),
                 ("Footprint", (c["fp"]).replace("NESPICO_RevC:", "NESPICO_RevC:"), 0, True), ("Datasheet", "", 0, True)]
        if not isflag:
            lc = design.LCSC.get(c["mpn"])
            props += [("MPN", c["mpn"], 0, True), ("LCSC", lc[0] if lc else "", 0, True),
                      ("LCSC_Status", lc[1] if lc else ("hand-assembly / not PCBA" if c["dnp"] else "no LCSC part"), 0, True), ("Note", c["note"], 0, True)]
        ptxt = " ".join(f'(property {q(k)} {q(v)} (at {f(cx)} {f(cy - dy)} 0) (effects (font (size 1.27 1.27)){" hide" if hide else ""}))' for k, v, dy, hide in props)
        pin_uuids = " ".join(f'(pin {q(p[0])} (uuid {q(U(c["ref"], "pin", p[0]))}))' for p in c["pins"])
        dnp = "yes" if c["dnp"] else "no"
        body.append(f'''(symbol (lib_id {q(lib_id)}) (at {f(cx)} {f(cy)} 0) (unit 1) (exclude_from_sim no) (in_bom {inb}) (on_board {inb}) (dnp {dnp}) (uuid {q(U(c["ref"]))})
  {ptxt} {pin_uuids}
  (instances (project {q(NAME)} (path {q("/" + ROOT)} (reference {q(c["ref"])}) (unit 1)))))''')
        for (num, pname, ptype), px, py, ang in geo:
            sx, sy = cx + px, cy - py
            net = c["nets"].get(num)
            if net:
                la = 180 if px < 0 else 0
                just = "right" if px < 0 else "left"
                body.append(f'(label {q(net)} (at {f(sx)} {f(sy)} {la}) (fields_autoplaced yes) (effects (font (size 1 1)) (justify {just} bottom)) (uuid {q(U(c["ref"], "lbl", num))}))')
            else:
                body.append(f'(no_connect (at {f(sx)} {f(sy)}) (uuid {q(U(c["ref"], "nc", num))}))')
    note = ("LASAGNA LITE: WeAct RP2350B Core Board + Rev.C cart circuit (dump-oriented, hand-solder). Generated with LASAGNA_LITE=1 from ../revc/design.py. " if design.LITE else "") + ("LASAGNA2354 (formerly NESPICO) Rev.C RP2354B board - PROPOSAL, NOT REVIEWED. Functional label-per-pin schematic generated by gen_sch.py from design.py. "
            "Unverified: Famicom slot footprint/mechanics, DA-15 expansion pinout, RCA footprint, timing. See README.md.")
    body.append(f'(text {q(note)} (exclude_from_sim no) (at 25.4 12.7 0) (effects (font (size 2 2)) (justify left bottom)) (uuid {q(U("note"))}))')
    sch = f'''(kicad_sch (version 20231120) (generator "nespico_gen") (generator_version "9.0") (uuid {q(ROOT)}) (paper "A0")
  (title_block (title {q("LASAGNA LITE (WeAct RP2350B) board (proposal)" if design.LITE else "LASAGNA2354 Rev.C RP2354B board (proposal)")}) (date "2026-10-13") (rev "C-draft1") (comment 1 "Not reviewed; not a fabrication sign-off"))
  (lib_symbols {" ".join(lib_forms.values())})
  {chr(10).join(body)}
  (sheet_instances (path "/" (page "1")))
)
'''
    (OUT / f"{NAME}.kicad_sch").write_text(sch)
    print("components", len(design.COMPS))

if __name__ == "__main__":
    if design.LITE:
        import gen_sch_lite; gen_sch_lite.main()
    else:
        main()

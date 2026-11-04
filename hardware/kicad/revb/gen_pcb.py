#!/usr/bin/env python3
"""Create NESPICO_RevB.kicad_pcb: footprints + nets + placement (routing done separately)."""
import pcbnew, design
from pathlib import Path
HERE = Path(__file__).parent
FPROOT = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM
OX, OY, W, H = 100.0, 100.0, 100.0, 100.0

def load(fpid):
    lib, name = fpid.split(":")
    path = str(HERE / "NESPICO_RevB.pretty") if lib == "NESPICO_RevB" else f"{FPROOT}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

# placement table: ref -> (x, y, rot) relative to board origin (mm)
P = {
    "J1": (6, 8, 0), "J2": (23.78, 8, 0),
    "J3": (13, 92, 90),
    "J5": (93, 33, 90), "J6": (91, 9, 0), "J7": (60, 3, 90),
    "SW1": (42, 3, 0), "Q1": (36, 4, 0), "F1": (30, 4, 0), "D1": (55, 4, 0),
    "J8": (33, 77, 90), "J9": (33, 83.5, 90), "J10": (4, 66, 90),
    "SJ3": (11, 30, 0), "SJ1": (15, 34, 0), "SJ2": (15, 38, 0),
}
ICS = ["U1","U2","U3","U9","U4","U5","U12","U10","U6","U7","U8","U11","U13","U14","U15","U16"]
for i, u in enumerate(ICS):
    P[u] = (35 + (i % 4) * 13.5, 13 + (i // 4) * 12.3, 0)

def main():
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nets = {}
    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
        return nets[n]
    others = []
    for c in design.COMPS:
        fp = load(c["fp"])
        fp.SetReference(c["ref"]); fp.SetValue(c["value"])
        lc = design.LCSC.get(c["mpn"])
        for k, v in (("LCSC", lc[0] if lc else ""), ("MPN", c["mpn"])):
            fld = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER if hasattr(pcbnew, "FIELD_T_USER") else 0, k) if False else None
            fp.SetField(k, v) if hasattr(fp, "SetField") else None
        if c["dnp"]:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for pad in fp.Pads():
            n = c["nets"].get(pad.GetNumber())
            if n: pad.SetNet(net(n))
        b.Add(fp)
        if c["ref"] in P:
            x, y, rot = P[c["ref"]]
            fp.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); fp.SetOrientationDegrees(rot)
        else:
            others.append(fp)
    # place passives: decouplers next to their IC, the rest in strips
    strip = [(31 + 2.0 * (i % 30), 63.5 + 3.6 * (i // 30)) for i in range(200)]
    k = 0
    for fp in others:
        ref = fp.GetReference(); c = next(x for x in design.COMPS if x["ref"] == ref)
        if c["note"].startswith("decouple "):
            ux, uy, _ = P[c["note"].split()[1]]
            fp.SetPosition(pcbnew.VECTOR2I(MM(OX + ux + 5.6), MM(OY + uy))); fp.SetOrientationDegrees(90)
        else:
            x, y = strip[k]; k += 1
            fp.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); fp.SetOrientationDegrees(90)
    # outline
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        a, c2 = pts[i], pts[(i + 1) % 4]
        s.SetStart(pcbnew.VECTOR2I(MM(OX + a[0]), MM(OY + a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(OX + c2[0]), MM(OY + c2[1])))
        s.SetWidth(MM(0.1)); b.Add(s)
    # net classes: power wider
    ds.m_TrackMinWidth = MM(0.15)
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass(); dflt.SetTrackWidth(MM(0.2)); dflt.SetClearance(MM(0.2)); dflt.SetViaDiameter(MM(0.6)); dflt.SetViaDrill(MM(0.3))
    pw = pcbnew.NETCLASS("Power"); pw.SetTrackWidth(MM(0.5)); pw.SetClearance(MM(0.2)); pw.SetViaDiameter(MM(0.8)); pw.SetViaDrill(MM(0.4))
    ns.SetNetclass("Power", pw)
    for n in ("GND", "VBUS", "+5V_LOGIC", "+5V_CART", "+3V3"):
        ns.SetNetclassPatternAssignment(n, "Power")
    for fp in b.GetFootprints():
        fp.Value().SetLayer(pcbnew.F_Fab)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); fp.Reference().SetTextThickness(MM(0.12))
    t = pcbnew.PCB_TEXT(b); t.SetText("NESPICO Rev.B bench DRAFT - not reviewed"); t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(pcbnew.VECTOR2I(MM(OX + 50), MM(OY + 98.5))); t.SetTextSize(pcbnew.VECTOR2I(MM(1), MM(1))); b.Add(t)
    b.Save(str(HERE / "NESPICO_RevB.kicad_pcb"))
    print("footprints", len(b.GetFootprints()), "nets", len(nets))

if __name__ == "__main__":
    main()

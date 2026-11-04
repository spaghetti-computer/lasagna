#!/usr/bin/env python3
"""JLCPCB BOM + CPL from the routed board. PCBA = SMD parts with LCSC numbers; THT/DNP excluded."""
import csv, collections, pcbnew, design
from pathlib import Path
HERE = Path(__file__).parent; FAB = HERE / "fab"
b = pcbnew.LoadBoard(str(HERE / "NESPICO_RevB.kicad_pcb"))
comps = {c["ref"]: c for c in design.COMPS}
groups = collections.OrderedDict(); cpl = []
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    c = comps[fp.GetReference()]
    lc = design.LCSC.get(c["mpn"])
    if c["dnp"] or not lc:
        continue
    key = (c["value"], fp.GetFPID().GetLibItemName().wx_str(), lc[0])
    groups.setdefault(key, []).append(c["ref"])
    p = fp.GetPosition(); o = b.GetDesignSettings().GetAuxOrigin()
    cpl.append([c["ref"], f"{pcbnew.ToMM(p.x):.3f}mm", f"{-pcbnew.ToMM(p.y):.3f}mm", "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom", f"{fp.GetOrientationDegrees() % 360:.1f}"])
with open(FAB / "NESPICO_RevB_BOM_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fpn, lcsc), refs in groups.items():
        w.writerow([val, ",".join(refs), fpn, lcsc])
with open(FAB / "NESPICO_RevB_CPL_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]); w.writerows(cpl)
with open(FAB / "NESPICO_RevB_hand_assembly.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Value", "Footprint", "Note"])
    for c in design.COMPS:
        if c["dnp"] or not design.LCSC.get(c["mpn"]):
            w.writerow([c["ref"], c["value"], c["fp"], c["note"]])
print("BOM lines", len(groups), "placed SMD", len(cpl))

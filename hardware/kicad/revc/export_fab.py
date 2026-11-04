#!/usr/bin/env python3
"""JLCPCB BOM + CPL from the routed board. PCBA = SMD parts with LCSC numbers; THT/DNP excluded."""
import csv, collections, pcbnew, design
from pathlib import Path
HERE = Path(__file__).parent
OUT, NAME = (HERE.parent / "revc_lite", "LASAGNA2354_Lite") if design.LITE else (HERE, "LASAGNA2354_RevC")
FAB = OUT / "fab"; FAB.mkdir(exist_ok=True)
b = pcbnew.LoadBoard(str(OUT / f"{NAME}.kicad_pcb"))
comps = {c["ref"]: c for c in design.COMPS if not c["ref"].startswith("TP")}  # TPs are bare pads, no BOM
groups = collections.OrderedDict(); cpl = []
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    c = comps.get(fp.GetReference())
    if c is None:
        continue          # fiducials / TPs (board-only)
    lc = design.LCSC.get(c["mpn"])
    if c["dnp"] or not lc:
        continue
    key = (c["value"], fp.GetFPID().GetLibItemName().wx_str(), lc[0])
    groups.setdefault(key, []).append(c["ref"])
    p = fp.GetPosition(); o = b.GetDesignSettings().GetAuxOrigin()
    cpl.append([c["ref"], f"{pcbnew.ToMM(p.x):.3f}mm", f"{-pcbnew.ToMM(p.y):.3f}mm", "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom", f"{fp.GetOrientationDegrees() % 360:.1f}"])
with open(FAB / f"{NAME}_BOM_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fpn, lcsc), refs in groups.items():
        w.writerow([val, ",".join(refs), fpn, lcsc])
with open(FAB / f"{NAME}_CPL_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]); w.writerows(cpl)
with open(FAB / f"{NAME}_hand_assembly.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Value", "Footprint", "Note"])
    for c in comps.values():
        if c["dnp"] or not design.LCSC.get(c["mpn"]):
            w.writerow([c["ref"], c["value"], c["fp"], c["note"]])
print("BOM lines", len(groups), "placed SMD", len(cpl))
if design.LITE:   # Lite is hand-built by default: one full BOM, every part with its source
    full = collections.OrderedDict()
    for c in comps.values():
        if c["ref"].startswith("H"): continue
        lc = design.LCSC.get(c["mpn"])
        full.setdefault((c["value"] + (" (DNP)" if c.get("nofit") else ""), c["fp"].split(":")[-1], lc[0] if lc else "", c["mpn"]), []).append(c["ref"])
    with open(FAB / f"{NAME}_BOM_FULL.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["Qty", "Value", "Designator", "Footprint", "LCSC", "MPN"])
        for (v, fpn, lc, mpn), refs in full.items():
            w.writerow([len(refs), v, ",".join(refs), fpn, lc, mpn])

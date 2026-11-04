"""Dump-only build (Leo 2026-10-13): PCBA = JLC *Basic* parts only; Extended parts are hand-soldered.
Basic/Extended is taken live from the JLC parts API (componentLibraryType base/expand); result cached in fab/jlc_parts_cache.json."""
import csv, json, pathlib, collections
from jlc_parts import q
import design
FAB = pathlib.Path(__file__).parent / "fab"
DUMP_DNP = {"J6", "R90", "R91", "R92",            # CVBS DAC + RCA
            "J9", "U10", "R51", "R52", "R53", "C27",  # Grove / MCP23017 + reset/I2C pull-ups + decap
            "J4", "J5", "R42", "R43"}              # pad headers + pad data pull-ups
cache_p = FAB / "jlc_parts_cache.json"
cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
def info(c):
    if c not in cache:
        L = [x for x in q(c) if x.get("componentCode") == c]
        x = L[0] if L else {}
        cache[c] = {"lib": x.get("componentLibraryType", "?"), "usd": (x.get("componentPrices") or [{}])[0].get("productPrice"),
                    "stock": x.get("stockCount"), "model": x.get("componentModelEn")}
    return cache[c]
cpl = {r["Designator"]: r for r in csv.DictReader(open(FAB / "LASAGNA2354_RevC_CPL_JLCPCB_PRE-ROUTE.csv"))}
basic, hand = collections.defaultdict(list), []
for c in design.COMPS:
    ref = c["ref"]
    if ref in DUMP_DNP or ref.startswith(("TP", "H", "FID")):
        continue
    lc = (design.LCSC.get(c["mpn"]) or (None,))[0]
    i = info(lc) if lc else {"lib": "none"}
    if lc and i["lib"] == "base" and not c["dnp"]:
        basic[(c["value"], c["fp"].split(":")[-1], lc)].append(ref)
    else:
        hand.append((ref, c["value"], c["mpn"], lc or "", i))
cache_p.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
refs = sorted(r for v in basic.values() for r in v)
with open(FAB / "LASAGNA2354_RevC_BOM_DUMP_BASIC.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (v, fp, lc), rs in sorted(basic.items()):
        w.writerow([v, ",".join(sorted(rs)), fp, lc])
with open(FAB / "LASAGNA2354_RevC_CPL_DUMP_BASIC.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in refs:
        w.writerow([cpl[r][k] for k in ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")])
usd = sum(cache[lc]["usd"] * len(rs) for (v, fp, lc), rs in basic.items())
print("basic lines", len(basic), "placed", len(refs), "parts $/board %.3f" % usd)
for h in hand: print("HAND", h[0], h[1], h[2], h[3], h[4].get("lib"), h[4].get("usd"), h[4].get("stock"))

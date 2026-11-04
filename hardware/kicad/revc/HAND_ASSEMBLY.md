# LASAGNA2354 Rev.C — hand-assembly list (PRE-ROUTE)

Parts that are **DNP for JLCPCB PCBA**. Fit them by hand (hot plate for the SMD part, iron for the THT parts).
Prices are as of 2026-10-13 and include tax.

| Ref | Part | Source | Code | Price | URL / note |
|---|---|---|---|---|---|
| L1 | AOTA-B201610S3R3-101-T 3.3uH (polarity-marked, the inductor the datasheet requires) | **Not at Akizuki.** LCSC C42411119 has 0 in stock. | — | — | Symmetry Electronics (~8k in stock) / Octopart. **Leo needs to choose.** Pad 1 (dot) = +1V1, copied from the RP2350 Minimal. Hot plate. |
| J6 | RCA jack MJ-526-Y (yellow) | Akizuki | 112477 | ¥30 | https://akizukidenshi.com/catalog/g/g112477/ — footprint built from the Avvicon drawing |
| J4, J5, J7 | Pin header 1×40, cut to 7/7/3 pins | Akizuki | 100167 | ¥35 | https://akizukidenshi.com/catalog/g/g100167/ (one strip covers all three) |
| J3 | Hirose CR22A-60D-2.54DS(70), 60-pin card-edge, through-hole | **Already owned** (bought at Sengoku) | — | — | Footprint built from the Hirose CR22 catalog D49647, pages A4/A6. Pad n = cart pin n. ⚠ The connector is rated for 1.6 mm cards; a Famicom cart PCB is 1.2 mm, so test the fit first. |
| (option) U10 | MCP23017-E/SP DIP28 | Akizuki | 109486 | ¥210 | https://akizukidenshi.com/catalog/g/g109486/ — only if the SSOP part (C506653) is out of stock at JLC. The DIP part does not fit the footprint (it would need a board revision). |
| (note) J9 | HY2.0-4P-WT (C722729) is assembled by JLC, but the footprint is **an approximate JST PH SM04B (kept as-is, Leo 10/13)**. | — | — | — | The drawing has no land pattern. Check the fit on the real part. |

## L1 substitute check: TDK NLV32T-3R3J-EF (Leo's candidate) → **NG, not adopted**
Source: TDK NLV-EF datasheet (LCSC copy C295115).

| Requirement (DS 6.3.8.2) | NLV32T-3R3J-EF | Result |
|---|---|---|
| 3.3 µH ±20% | 3.3 µH ±5% | OK |
| DCR ≤ 250 mΩ | 1.2 Ω max | **NG** (about 5×) |
| Isat ≥ 1.5 A | rated 260 mA (10% L drop or ΔT 20 °C) | **NG** (about 1/6) |
| Shielded | unshielded wire-wound ferrite | **NG** |
| Polarity marking | none | **NG** |

Stock: LCSC C295115 has about 2,300; Akizuki and Sengoku have none.
It is a signal/filter inductor, not a power inductor. At the 1.1 V buck's peak current it would saturate and heat up, and the DCR losses would drop efficiency and output voltage. Without shielding and a polarity mark, the switching node can couple noise into the crystal and ADC. The design therefore stays on the AOTA part, and the footprint is unchanged.
It is not suitable even as an experimental fallback. It might run at low load, but brown-outs or resets are likely once the core is heavily loaded.
If a stopgap is needed, choose a **shielded 3.3 µH, Isat ≥ 1.5 A, DCR ≤ 250 mΩ** part (for example a 2520/3225 metal-composite type). A dual footprint covering the 2016 AOTA and a 3225 part is possible but has not been built yet (Leo's decision).

"""NESPICO Rev.B bench board: single source of truth for schematic + PCB.

PROPOSAL / bench board. Not reviewed. See README.md for unverified items.
"""
# ---------- pin tables (number, name, type) ----------
def ic574():
    p = [("1", "OE_N", "input")] + [(str(2 + i), f"D{i}", "input") for i in range(8)]
    p += [("10", "GND", "power_in"), ("11", "CLK", "input")]
    p += [(str(19 - i), f"Q{i}", "tri_state") for i in range(8)] + [("20", "VCC", "power_in")]
    return p
def ic245():
    p = [("1", "DIR", "input")] + [(str(2 + i), f"A{i+1}", "bidirectional") for i in range(8)]
    p += [("10", "GND", "power_in")] + [(str(18 - i), f"B{i+1}", "bidirectional") for i in range(8)]
    return p + [("19", "OE_N", "input"), ("20", "VCC", "power_in")]
def ic541():
    p = [("1", "OE1_N", "input")] + [(str(2 + i), f"A{i+1}", "input") for i in range(8)]
    p += [("10", "GND", "power_in")] + [(str(18 - i), f"Y{i+1}", "tri_state") for i in range(8)]
    return p + [("19", "OE2_N", "input"), ("20", "VCC", "power_in")]
def ic04():
    return [("1","1A","input"),("2","1Y","output"),("3","2A","input"),("4","2Y","output"),("5","3A","input"),("6","3Y","output"),("7","GND","power_in"),("8","4Y","output"),("9","4A","input"),("10","5Y","output"),("11","5A","input"),("12","6Y","output"),("13","6A","input"),("14","VCC","power_in")]
def ic32():
    return [("1","1A","input"),("2","1B","input"),("3","1Y","output"),("4","2A","input"),("5","2B","input"),("6","2Y","output"),("7","GND","power_in"),("8","3Y","output"),("9","3A","input"),("10","3B","input"),("11","4Y","output"),("12","4A","input"),("13","4B","input"),("14","VCC","power_in")]
def ic74():
    return [("1","1CLR_N","input"),("2","1D","input"),("3","1CLK","input"),("4","1PRE_N","input"),("5","1Q","output"),("6","1Q_N","output"),("7","GND","power_in"),("8","2Q_N","output"),("9","2Q","output"),("10","2PRE_N","input"),("11","2CLK","input"),("12","2D","input"),("13","2CLR_N","input"),("14","VCC","power_in")]
def ic139():
    return [("1","1G_N","input"),("2","1A","input"),("3","1B","input"),("4","1Y0","output"),("5","1Y1","output"),("6","1Y2","output"),("7","1Y3","output"),("8","GND","power_in"),("9","2Y3","output"),("10","2Y2","output"),("11","2Y1","output"),("12","2Y0","output"),("13","2B","input"),("14","2A","input"),("15","2G_N","input"),("16","VCC","power_in")]
def ic165():
    return [("1","SH_LD_N","input"),("2","CLK","input"),("3","E","input"),("4","F","input"),("5","G","input"),("6","H","input"),("7","QH_N","output"),("8","GND","power_in"),("9","QH","output"),("10","SER","input"),("11","A","input"),("12","B","input"),("13","C","input"),("14","D","input"),("15","CLK_INH","input"),("16","VCC","power_in")]
def ic595():
    return [("1","QB","output"),("2","QC","output"),("3","QD","output"),("4","QE","output"),("5","QF","output"),("6","QG","output"),("7","QH","output"),("8","GND","power_in"),("9","QH_P","output"),("10","SRCLR_N","input"),("11","SRCLK","input"),("12","RCLK","input"),("13","OE_N","input"),("14","SER","input"),("15","QA","output"),("16","VCC","power_in")]
def conn(n, prefix="P"):
    return [(str(i), f"{prefix}{i}", "passive") for i in range(1, n + 1)]
TWO = [("1", "1", "passive"), ("2", "2", "passive")]

FP = {
    "TSSOP20": "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
    "TSSOP14": "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
    "SOIC14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "SOIC16": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "F1206": "Fuse:Fuse_1206_3216Metric",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOCK20": "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical",
    "HDR2x30": "Connector_PinHeader_2.54mm:PinHeader_2x30_P2.54mm_Vertical",
    "HDR2x20": "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
    "HDR2x08": "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical",
    "HDR1x02": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "DA15": "Connector_Dsub:DSUB-15_Socket_Horizontal_P2.77x2.84mm_EdgePinOffset9.40mm",
    "RCA": "NESPICO_RevB:RCA_Jack_Generic_THT_UNVERIFIED",
    "SLIDE": "Button_Switch_THT:SW_DIP_SPSTx01_Slide_6.7x4.1mm_W7.62mm_P2.54mm_LowProfile",
    "SJ2C": "Jumper:SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm",
    "SJ3": "Jumper:SolderJumper-3_P1.3mm_Bridged12_Pad1.0x1.5mm",
}
# LCSC numbers: "verified" = product page title fetched 2026-10-13 and matches MPN.
LCSC = {
    "SN74AHCT574PWR": ("C129433", "verified; JLC Extended, page showed stock 0 at check"),
    "74LVC245APW,118": ("C6082", "verified"),
    "74LVC541APW,118": ("C6093", "verified"),
    "74HCT04D,653": ("C672096", "verified"),
    "74HCT74D,653": ("C686657", "verified"),
    "74HCT139D,653": ("C545677", "verified (datasheet link)"),
    "74AHCT32PW,118": ("C554656", "verified"),
    "74HC165D,653": ("C5613", "verified"),
    "74HC595D,118": ("C5947", "verified"),
    "AO3401A": ("C15127", "verified"),
    "SMD1206-050-6": ("C46641012", "verified (search page)"),
    "10k": ("C25804", "verified 0603WAF1002T5E"),
    "1k": ("C21190", "verified 0603WAF1001T5E"),
    "220": ("C22962", "verified 0603WAF2200T5E"),
    "470": ("C23179", "verified 0603WAF4700T5E"),
    "910": ("C23264", "verified 0603WAF9100T5E"),
    "100nF": ("C14663", "verified CC0603KRX7R9BB104"),
    "10uF": ("C15850", "verified CL21A106KAYNNNE"),
    "LED_G": ("C72043", "verified 19-217/GHC-YR1S2/3T"),
}

COMPS = []   # dicts: ref, sym, pins, fp, value, mpn, nets{num:net}, dnp, note
def add(ref, sym, pins, fp, value, nets, mpn="", dnp=False, note=""):
    nums = {p[0] for p in pins}
    for k in nets:
        assert k in nums, (ref, k)
    COMPS.append(dict(ref=ref, sym=sym, pins=pins, fp=FP[fp], value=value, mpn=mpn, nets=nets, dnp=dnp, note=note))

V5, V3, VB, G = "+5V_LOGIC", "+3V3", "VBUS", "GND"
VC = "+5V_CART"
# ---------- Pico 2 (socketed) ----------
pico = {1:"CD0",2:"CD1",3:G,4:"CD2",5:"CD3",6:"CD4",7:"CD5",8:G,9:"CD6",10:"CD7",11:"PD0",12:"PD1",13:G,14:"PD2",15:"PD3",16:"PD4",17:"PD5",18:G,19:"PD6",20:"PD7",
        21:"M2",22:"CPU_ALE",23:G,24:"PPU_ALE",25:"PPU_STB_N",26:"CVBS_B0",27:"CVBS_B1",28:G,29:"CVBS_B2",30:None,31:"AUDIO_ADC",32:None,33:G,34:None,35:None,36:V3,37:None,38:G,39:None,40:VB}
add("J1", "PICO_L", conn(20, "GP"), "SOCK20", "Pico2_pins1-20", {str(i): pico[i] for i in range(1, 21) if pico[i]}, dnp=True, note="hand-solder socket")
add("J2", "PICO_R", conn(20, "P"), "SOCK20", "Pico2_pins40-21", {str(k): pico[41 - k] for k in range(1, 21) if pico[41 - k]}, dnp=True, note="pad k = Pico pin 41-k")
# ---------- cartridge 60-pin ----------
cart = {1:G,2:"CA11",3:"CA10",4:"CA9",5:"CA8",6:"CA7",7:"CA6",8:"CA5",9:"CA4",10:"CA3",11:"CA2",12:"CA1",13:"CA0",14:"CPU_RW",15:"IRQ_N",16:G,17:"PPU_RD_N",18:"CIRAM_A10",
        19:"PA6",20:"PA5",21:"PA4",22:"PA3",23:"PA2",24:"PA1",25:"PA0",26:"XPD0",27:"XPD1",28:"XPD2",29:"XPD3",30:VC,31:None,32:"M2_CART",33:"CA12",34:"CA13",35:"CA14",
        36:"XCD7",37:"XCD6",38:"XCD5",39:"XCD4",40:"XCD3",41:"XCD2",42:"XCD1",43:"XCD0",44:"ROMSEL_N",45:"AUDIO_IN_BIAS",46:"AUDIO_RET",47:"PPU_WR_N",48:"CIRAM_CE_N",
        49:"PA13_N",50:"PA7",51:"PA8",52:"PA9",53:"PA10",54:"PA11",55:"PA12",56:"PA13",57:"XPD7",58:"XPD6",59:"XPD5",60:"XPD4"}
cpins = [(str(2*n-1 if n<=30 else 2*(n-30)), f"C{n}", "passive") for n in range(1, 61)]
cnets = {}
for n, net in cart.items():
    if net: cnets[str(2*n-1 if n<=30 else 2*(n-30))] = net
add("J3", "FAMICOM60", cpins, "HDR2x30", "Famicom_60pin_slot", cnets, dnp=True,
    note="PLACEHOLDER footprint: 2x30 2.54mm header grid; real slot row spacing/mechanics UNVERIFIED")
# ---------- latches ----------
def latch(ref, d, q, clk, oe, vcc=V5):
    nets = {"1": oe, "10": G, "11": clk, "20": vcc}
    for i in range(8):
        nets[str(2+i)] = d[i]
        if q[i]: nets[str(19-i)] = q[i]
    return nets
CD = [f"CD{i}" for i in range(8)]; PD = [f"PD{i}" for i in range(8)]
add("U1","74AHCT574",ic574(),"TSSOP20","SN74AHCT574PWR",latch("U1",CD,[f"CA{i}" for i in range(8)],"CLK_CA_LO","CART_G"),"SN74AHCT574PWR")
add("U2","74AHCT574",ic574(),"TSSOP20","SN74AHCT574PWR",latch("U2",CD,[f"CA{i}" for i in range(8,15)]+["A15_N"],"CLK_CA_HI","CART_G"),"SN74AHCT574PWR")
add("U3","74AHCT574",ic574(),"TSSOP20","SN74AHCT574PWR",latch("U3",CD,["CPU_RW","SR_CLK","SR_LD","SR_SER","STATUS_SEL_N","CTL_SP5","CTL_SP6","CTL_SP7"],"CLK_CTL","CART_G"),"SN74AHCT574PWR")
add("U4","74AHCT574",ic574(),"TSSOP20","SN74AHCT574PWR",latch("U4",PD,[f"PA{i}" for i in range(8)],"CLK_PA_LO","CART_G"),"SN74AHCT574PWR")
add("U5","74AHCT574",ic574(),"TSSOP20","SN74AHCT574PWR",latch("U5",PD,[f"PA{i}" for i in range(8,14)]+["RD_SEL_N","WR_SEL_N"],"CLK_PA_HI","CART_G"),"SN74AHCT574PWR")
# ---------- data transceivers (3.3 V, 5 V tolerant, Ioff) ----------
def xcvr(dirn, a, b, oe):
    nets = {"1": dirn, "10": G, "19": oe, "20": V3}
    for i in range(8):
        nets[str(2+i)] = a[i]; nets[str(18-i)] = b[i]
    return nets
add("U6","74LVC245",ic245(),"TSSOP20","74LVC245APW",xcvr("CPU_DIR",CD,[f"XCD{i}" for i in range(8)],"M2_N"),"74LVC245APW,118")
add("U7","74LVC245",ic245(),"TSSOP20","74LVC245APW",xcvr("RD_SEL_N",PD,[f"XPD{i}" for i in range(8)],"PPU_STB_N"),"74LVC245APW,118")
st = {"1":"STATUS_SEL_N","19":"STB_ACT","10":G,"20":V3}
ins = ["IRQ_N","CIRAM_A10","CIRAM_CE_N","STAT_IN4",G,G,G,G]
for i in range(8):
    st[str(2+i)] = ins[i]; st[str(18-i)] = PD[i]
add("U8","74LVC541",ic541(),"TSSOP20","74LVC541APW",st,"74LVC541APW,118")
# ---------- control logic (5 V logic rail, always on from VBUS) ----------
add("U9","74HCT04",ic04(),"SOIC14","74HCT04D",{"1":"CPU_ALE","2":"CPU_ALE_N","3":"PPU_ALE","4":"PPU_ALE_N","5":"M2","6":"M2_N","7":G,"9":"CPU_RW","8":"CPU_DIR","11":"PPU_STB_N","10":"STB_ACT","13":"PA13","12":"PA13_N","14":V5},"74HCT04D,653")
add("U10","74HCT74",ic74(),"SOIC14","74HCT74D",{"1":"M2_N","2":"PH2_N","3":"CPU_ALE_N","4":V5,"5":"PH1","7":G,"8":"PH2_N","9":"PH2","10":V5,"11":"CPU_ALE_N","12":"PH1","13":"M2_N","14":V5},"74HCT74D,653")
add("U11","74HCT74",ic74(),"SOIC14","74HCT74D",{"1":"PPU_STB_N","2":"PPH_N","3":"PPU_ALE_N","4":V5,"5":"PPH","6":"PPH_N","7":G,"10":V5,"11":G,"12":G,"13":V5,"14":V5},"74HCT74D,653")
add("U12","74HCT139",ic139(),"SOIC16","74HCT139D",{"1":"CPU_ALE_N","2":"PH1","3":"PH2","4":"CLK_CA_LO","5":"CLK_CA_HI","7":"CLK_CTL","8":G,"15":"PPU_ALE_N","14":"PPH","13":G,"12":"CLK_PA_LO","11":"CLK_PA_HI","16":V5},"74HCT139D,653")
add("U13","74AHCT32",ic32(),"TSSOP14","74AHCT32PW",{"1":"PPU_STB_N","2":"RD_SEL_N","3":"PPU_RD_N","4":"PPU_STB_N","5":"WR_SEL_N","6":"PPU_WR_N","7":G,"9":"A15_N","10":"M2_N","8":"ROMSEL_N","12":"M2","13":G,"11":"M2_CART","14":VC},"74AHCT32PW,118",
    note="powered from +5V_CART; AHCT inputs are overvoltage tolerant")
# ---------- shift chain (expansion port / controllers) ----------
add("U14","74HC165",ic165(),"SOIC16","74HC165D",{"1":"SR_LD","2":"SR_CLK","15":G,"10":"SRQ_MID","11":"J4017_D0","12":"J4017_D1","13":"J4017_D2","14":"J4017_D3","3":"J4017_D4","4":"J4016_D1","5":"EXP_IN_SP1","6":"EXP_IN_SP2","9":"SR_QH","8":G,"16":V5},"74HC165D,653")
add("U15","74HC165",ic165(),"SOIC16","74HC165D",{"1":"SR_LD","2":"SR_CLK","15":G,"10":G,**{k:f"SR_IN{j}" for k,j in zip(["11","12","13","14","3","4","5","6"],range(9,17))},"9":"SRQ_MID","8":G,"16":V5},"74HC165D,653")
add("U16","74HC595",ic595(),"SOIC16","74HC595D",{"14":"SR_SER","11":"SR_CLK","12":"SR_LD","13":G,"10":V5,"15":"EXP_OUT0","1":"EXP_OUT1","2":"EXP_OUT2","3":"J4016_OE_N","4":"J4017_OE_N","5":"SRO_SP6","6":"SRO_SP7","7":"SRO_SP8","8":G,"16":V5},"74HC595D,118")
# Status input 4 select: SR_QH (shift chain, default) or EXP_PAR_IN (alt parallel source from header)
add("SJ3","SJ3",[("1","A","passive"),("2","C","passive"),("3","B","passive")],"SJ3","SR_QH|STAT|PAR",{"1":"SR_QH","2":"STAT_IN4","3":"EXP_PAR_IN"},note="default 1-2 bridged = shift chain")
# ---------- expansion port DA-15 (pinout UNVERIFIED) ----------
exp = {1:G,2:"AUDIO_RET",3:"IRQ_N",4:"J4017_D4",5:"J4017_D3",6:"J4017_D2",7:"J4017_D1",8:"J4017_D0",9:"J4017_OE_N",10:"EXP_OUT2",11:"EXP_OUT1",12:"EXP_OUT0",13:"J4016_D1",14:"J4016_OE_N",15:VC}
add("J5","DA15",conn(15)+[("0","MH","passive")],"DA15","Famicom_expansion_DA15",{str(k):v for k,v in exp.items()} | {"0": G},dnp=True,note="pinout from memory of NESdev; VERIFY")
# ---------- CVBS ----------
add("R90","R",TWO,"R0603","910",{"1":"CVBS_B0","2":"CVBS"},"910")
add("R91","R",TWO,"R0603","470",{"1":"CVBS_B1","2":"CVBS"},"470")
add("R92","R",TWO,"R0603","220",{"1":"CVBS_B2","2":"CVBS"},"220")
add("J6","RCA",[("1","SIG","passive"),("2","GND","passive")],"RCA","RCA_CVBS",{"1":"CVBS","2":G},dnp=True,note="generic footprint UNVERIFIED vs actual jack")
add("J7","HDR2",TWO,"HDR1x02","CVBS_ALT",{"1":"CVBS","2":G},dnp=True)
# ---------- audio ----------
add("R93","R",TWO,"R0603","10k",{"1":"AUDIO_RET","2":"AUDIO_ADC"},"10k")
add("R94","R",TWO,"R0603","10k",{"1":"AUDIO_ADC","2":G},"10k")
add("R95","R",TWO,"R0603","10k",{"1":VC,"2":"AUDIO_IN_BIAS"},"10k")
add("R96","R",TWO,"R0603","10k",{"1":"AUDIO_IN_BIAS","2":G},"10k")
# ---------- power: polyfuse + P-MOSFET cart switch ----------
add("F1","FUSE",TWO,"F1206","500mA_PTC",{"1":VB,"2":V5},"SMD1206-050-6",note="+5V_LOGIC = fused VBUS (always on)")
add("Q1","PMOS",[("1","G","input"),("2","S","passive"),("3","D","passive")],"SOT23","AO3401A",{"1":"CART_G","2":V5,"3":VC},"AO3401A")
add("R97","R",TWO,"R0603","10k",{"1":"CART_G","2":V5},"10k")
add("R98","R",TWO,"R0603","1k",{"1":"CART_G","2":"CART_SW"},"1k")
add("SW1","SW",TWO,"SLIDE","CART_PWR",{"1":"CART_SW","2":G},dnp=True,note="closed = cart power ON; also enables latch OE (CART_G low)")
add("R99","R",TWO,"R0603","1k",{"1":VC,"2":"LED_A"},"1k")
add("D1","LED",[("1","K","passive"),("2","A","passive")],"LED0603","CART_ON",{"1":G,"2":"LED_A"},"LED_G")
add("C1","C",TWO,"C0805","10uF",{"1":V5,"2":G},"10uF")
add("C2","C",TWO,"C0805","10uF",{"1":VC,"2":G},"10uF")
add("C3","C",TWO,"C0805","10uF",{"1":V3,"2":G},"10uF")
# decoupling
for i, (u, rail) in enumerate([("U1",V5),("U2",V5),("U3",V5),("U4",V5),("U5",V5),("U6",V3),("U7",V3),("U8",V3),("U9",V5),("U10",V5),("U11",V5),("U12",V5),("U13",VC),("U14",V5),("U15",V5),("U16",V5)]):
    add(f"C{10+i}","C",TWO,"C0603","100nF",{"1":rail,"2":G},"100nF",note=f"decouple {u}")
# ---------- external pulls (RP2350 E9: internal pull-down unusable) ----------
r = 1
def res(a, b, val="10k", note=""):
    global r
    add(f"R{r}","R",TWO,"R0603",val,{"1":a,"2":b},val,note=note); r += 1
for n in CD: res(n, "PU_CPU")
for n in PD: res(n, "PU_PPU")
add("SJ1","SJ2",TWO,"SJ2C","PU_CPU_EN",{"1":"PU_CPU","2":V3},note="cut to remove CPU lane pull-ups")
add("SJ2","SJ2",TWO,"SJ2C","PU_PPU_EN",{"1":"PU_PPU","2":V3},note="cut to remove PPU lane pull-ups")
res("M2", G); res("CPU_ALE", G); res("PPU_ALE", G); res("PPU_STB_N", V3)
res("IRQ_N", VC); res("CIRAM_A10", G); res("CIRAM_CE_N", VC)
for n in ["J4017_D0","J4017_D1","J4017_D2","J4017_D3","J4017_D4","J4016_D1","EXP_IN_SP1","EXP_IN_SP2"]: res(n, V5)
for j in range(9, 17): res(f"SR_IN{j}", V5)
res("CPU_RW", VC); res("STATUS_SEL_N", V3); res("SR_CLK", G); res("SR_LD", G); res("SR_SER", G)
res("EXP_PAR_IN", V3)
assert r < 90, r
# ---------- bench test-point headers (THT, hand-solder) ----------
tp1 = CD + PD + ["M2_CART","CPU_ALE","PPU_ALE","PPU_STB_N","ROMSEL_N","PPU_RD_N","PPU_WR_N","CPU_RW","IRQ_N","CIRAM_A10","CIRAM_CE_N","STATUS_SEL_N","CLK_CA_LO","CLK_CA_HI","CLK_CTL","CLK_PA_LO","CLK_PA_HI","M2_N","STB_ACT","CART_G",G,G,G,G]
tp2 = [f"CA{i}" for i in range(15)] + ["A15_N"] + [f"PA{i}" for i in range(14)] + ["PA13_N","RD_SEL_N","WR_SEL_N","XCD0","XPD0","AUDIO_RET",VC,V3,G,G]
tp3 = [f"SR_IN{j}" for j in range(9,17)] + ["SRO_SP6","SRO_SP7","SRO_SP8","CTL_SP5","CTL_SP6","CTL_SP7","EXP_PAR_IN",G]
add("J8","HDR40",conn(40),"HDR2x20","TP_BUS_CTRL",{str(i+1):n for i,n in enumerate(tp1)},dnp=True)
add("J9","HDR40",conn(40),"HDR2x20","TP_ADDR",{str(i+1):n for i,n in enumerate(tp2)},dnp=True)
add("J10","HDR16",conn(16),"HDR2x08","TP_SR_SPARE",{str(i+1):n for i,n in enumerate(tp3)},dnp=True)
assert len(tp1) == 40 and len(tp2) == 40 and len(tp3) == 16

"""NESPICO Rev.C: bare RP2354B + 7 AHCT logic ICs. Single source of truth for schematic + PCB.

PROPOSAL. Not reviewed. See README.md / ../revc-plan.md.
"""
def ic245():
    p = [("1", "DIR", "input")] + [(str(2 + i), f"A{i+1}", "bidirectional") for i in range(8)]
    p += [("10", "GND", "power_in")] + [(str(18 - i), f"B{i+1}", "bidirectional") for i in range(8)]
    return p + [("19", "OE_N", "input"), ("20", "VCC", "power_in")]
def ic541():
    p = [("1", "OE1_N", "input")] + [(str(2 + i), f"A{i+1}", "input") for i in range(8)]
    p += [("10", "GND", "power_in")] + [(str(18 - i), f"Y{i+1}", "tri_state") for i in range(8)]
    return p + [("19", "OE2_N", "input"), ("20", "VCC", "power_in")]
def conn(n, prefix="P"):
    return [(str(i), f"{prefix}{i}", "passive") for i in range(1, n + 1)]
TWO = [("1", "1", "passive"), ("2", "2", "passive")]

def ic573():
    p = [("1", "OE_N", "input")] + [(str(2 + i), f"D{i}", "input") for i in range(8)]
    p += [("10", "GND", "power_in"), ("11", "LE", "input")]
    p += [(str(19 - i), f"Q{i}", "tri_state") for i in range(8)] + [("20", "VCC", "power_in")]
    return p

# ---- RP2354B QFN-80 (RP2350 datasheet Table 1674-1679 + Fig.3; pin 60/76 = IOVDD from Fig.3) ----
GPIO_PIN = {0:77,1:78,2:79,3:80,4:1,5:2,6:3,7:4,8:6,9:7,10:8,11:9,12:11,13:12,14:13,15:14,16:16,17:17,18:18,19:19,
            20:20,21:21,22:22,23:23,24:25,25:26,26:27,27:28,28:36,29:37,30:38,31:39,32:40,33:42,34:43,35:44,36:45,
            37:46,38:47,39:48,40:49,41:52,42:53,43:54,44:55,45:56,46:57,47:58}
RP_OTHER = {30:"XIN",31:"XOUT",33:"SWCLK",34:"SWDIO",35:"RUN",66:"USB_DM",67:"USB_DP",59:"ADC_AVDD",61:"VREG_AVDD",
            62:"VREG_PGND",63:"VREG_LX",64:"VREG_VIN",65:"VREG_FB",68:"USB_OTP_VDD",69:"QSPI_IOVDD",70:"QSPI_SD3",
            71:"QSPI_SCLK",72:"QSPI_SD0",73:"QSPI_SD2",74:"QSPI_SD1",75:"QSPI_SS",81:"GND_EP"}
for n in (10, 32, 51): RP_OTHER[n] = "DVDD"
for n in (5, 15, 24, 29, 41, 50, 60, 76): RP_OTHER[n] = "IOVDD"
def ic_rp():
    names = {v: f"GPIO{k}" for k, v in GPIO_PIN.items()} | RP_OTHER
    assert sorted(names) == list(range(1, 82))
    pw = {"DVDD","IOVDD","ADC_AVDD","VREG_AVDD","VREG_PGND","VREG_VIN","USB_OTP_VDD","QSPI_IOVDD","GND_EP"}
    return [(str(n), names[n], "power_in" if names[n] in pw else ("passive" if names[n] in ("VREG_LX","XIN","XOUT","VREG_FB") else "bidirectional")) for n in range(1, 82)]

FP = {
    "QFN80": "Package_DFN_QFN:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm",
    "TSSOP20": "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
    "R0603": "Resistor_SMD:R_0603_1608Metric", "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric", "LED0603": "LED_SMD:LED_0603_1608Metric",
    "F1206": "Fuse:Fuse_1206_3216Metric", "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT223": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "XTAL": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "L2016": "Inductor_SMD:L_Murata_DFE201610P",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "BTN": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "HDR2x30": "Connector_PinHeader_2.54mm:PinHeader_2x30_P2.54mm_Vertical", "CR22A60": "NESPICO_RevC:Hirose_CR22A-60D-2.54DS",
    "HDR2x20": "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
    "HDR1x07": "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
    "HDR1x03": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "HDR1x02": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "RCA": "NESPICO_RevC:RCA_Jack_Generic_THT_UNVERIFIED",
    "SSOP28": "Package_SO:SSOP-28_5.3x10.2mm_P0.65mm",
    # copied 1:1 from the official RP2350 Minimal design R4 (MIT): regulator + crystal parts
    "L_AOTA": "NESPICO_RevC:RPi_AOTA-B201610S3R3-101-T", "C1005W": "NESPICO_RevC:RPi_C_1005_wide",
    "R1005": "NESPICO_RevC:RPi_R_1005", "XTAL_RPI": "NESPICO_RevC:RPi_XTAL_3225-4",
    "RCA_MJ526": "NESPICO_RevC:RCA_Avvicon_MJ-526",
    "GROVE": "Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal",
}
# LCSC numbers: verified = LCSC product page / search result title matched MPN, 2026-10-13.
LCSC = {
    # 0402 parts for the copied regulator/crystal section (LCSC page titles checked 2026-10-13)
    "4.7uF-0402": ("C23733", "verified CL05A475MP5NRNC"), "33R-0402": ("C25105", "verified 0402WGF330JTCE"),
    "27R-0402": ("C25100", "verified 0402WGF270JTCE"), "1k-0402": ("C11702", "verified 0402WGF1001TCE"),
    "15pF-0402": ("C1548", "verified 0402CG150J500NT"), "100nF-0402": ("C1525", "verified CL05B104KO5NNNC"),
    "XC61CN3002MR-G": ("C2456348", "verified JLC Extended"),
    "MCP23017-E/SS": ("C506653", "verified LCSC page 2026-10-13, stock ~995 (aggregator showed 97)"),
    "HY2.0-4P-WT": ("C722729", "LCSC page found; footprint = JST PH SMD R/A stand-in, UNVERIFIED"),
    "RP2354B": ("C39843328", "verified; LCSC stock ~3.2k"),
    "SN74AHCT573PWR": ("C141311", "verified JLC stock 1830 (Nexperia C282327 had JLC stock 0)"),
    "74AHCT245PW,118": ("C173388", "verified"),
    "74AHCT541PW,118": ("C84548", "verified; JLC Extended, stock ~20.9k"),
    "SN74AHCT540PWR": ("C7626", "verified"),
    "NCP1117ST33T3G": ("C26537", "verified (HDG minimal-design LDO)"),
    "ABM8-272-T3": ("C20625731", "verified (HDG recommended crystal)"),
    "AOTA-B201610S3R3-101-T": ("C42411119", "verified (HDG inductor); LCSC stock 0 at check"),
    "TYPE-C-31-M-12": ("C165948", "verified"),
    "TS-1187A-B-A-B": ("C318884", "verified"),
    "2N7002": ("C8545", "verified"),
    "AO3401A": ("C15127", "verified (Rev.B)"),
    "SMD1206-050-6": ("C46641012", "verified (Rev.B)"),
    "4.7k": ("C23162", "verified 0603WAF4701T5E (JLC Basic)"), "10k": ("C25804", "verified"), "1k": ("C21190", "verified"), "220": ("C22962", "verified"),
    "470": ("C23179", "verified"), "910": ("C23264", "verified"), "27": ("C25190", "verified"),
    "33": ("C23140", "verified"), "5.1k": ("C23186", "verified"),
    "100nF": ("C14663", "verified"), "10uF": ("C15850", "verified"), "4.7uF": ("C19666", "verified"),
    "15pF": ("C1644", "verified"), "LED_G": ("C2286", "JLC Basic KT-0603R red (C72043 green is EOL, stock 1); verified via JLC API 2026-10-13"),
}
COMPS = []
def add(ref, sym, pins, fp, value, nets, mpn="", dnp=False, note=""):
    nums = {p[0] for p in pins}
    for k in nets: assert k in nums, (ref, k)
    COMPS.append(dict(ref=ref, sym=sym, pins=pins, fp=FP[fp], value=value, mpn=mpn, nets=nets, dnp=dnp, note=note))

G, V3, VB, V5, VC, V11 = "GND", "+3V3", "VBUS", "+5V_LOGIC", "+5V_CART", "+1V1"
OE = "OUT_OE_N"
# ---- GPIO allocation (revc-plan.md section 2b) ----
gp = {}
for i in range(8): gp[i] = f"CADM{i}"           # CPU AD (MCU side of 33R)
for i in range(7): gp[8+i] = f"GA{8+i}"         # CPU A8-14 (3.3 V, to U6)
gp.update({15:"G_RW",16:"G_ROMSEL_N",17:"G_M2_N",18:"CPU_ALE"})
for i in range(8): gp[19+i] = f"PADM{i}"
for i in range(6): gp[27+i] = f"GPA{8+i}"
gp.update({33:"PPU_DEN_N",34:"G_RD",35:"G_WR_N",36:"PPU_ALE",37:"IRQ_N",38:"CIRAM_A10",39:"CIRAM_CE_N",
           40:"CVBS_B0",41:"CVBS_B1",42:"CVBS_B2",43:"CART_EN_G",44:"I2C_SDA",45:"I2C_SCL",46:"SPARE_GP46",47:"SPARE_GP47"})
# GPIO44/45 = I2C0 SDA/SCL (RP2350 function F3). Pads now go through U10 MCP23017. GPIO46/47 are spare (3.3 V only, ADC pads).
assert len(gp) == 48
rp = {str(GPIO_PIN[k]): v for k, v in gp.items()}
rp.update({"30":"XIN","31":"XOUT_M","33":"SWCLK","34":"SWDIO","35":"RUN","66":"USB_DM_C","67":"USB_DP_C",
           "59":V3,"61":"VREG_AVDD","62":G,"63":"VREG_LX","64":V3,"65":V11,"68":V3,"69":V3,"75":"QSPI_SS","81":G})
for n in (10, 32, 51): rp[str(n)] = V11
for n in (5, 15, 24, 29, 41, 50, 60, 76): rp[str(n)] = V3
add("U1","RP2354B",ic_rp(),"QFN80","RP2354B",rp,"RP2354B",note="QSPI_SD0-3/SCLK NC: flash is in-package")
# ---- cartridge slot ----
cart = {1:G,2:"CA11",3:"CA10",4:"CA9",5:"CA8",6:"CA7",7:"CA6",8:"CA5",9:"CA4",10:"CA3",11:"CA2",12:"CA1",13:"CA0",14:"CART_RW",15:"IRQ_N",16:G,17:"CART_RD_N",18:"CIRAM_A10",
        19:"PA6",20:"PA5",21:"PA4",22:"PA3",23:"PA2",24:"PA1",25:"PA0",26:"XPD0",27:"XPD1",28:"XPD2",29:"XPD3",30:VC,32:"M2_CART",33:"CA12",34:"CA13",35:"CA14",
        36:"XCD7",37:"XCD6",38:"XCD5",39:"XCD4",40:"XCD3",41:"XCD2",42:"XCD1",43:"XCD0",44:"CART_ROMSEL_N",47:"CART_WR_N",48:"CIRAM_CE_N",
        49:"PA13_N",50:"PA7",51:"PA8",52:"PA9",53:"PA10",54:"PA11",55:"PA12",56:"PA13",57:"XPD7",58:"XPD6",59:"XPD5",60:"XPD4"}
pad = lambda n: str(n)          # Hirose CR22A footprint: pad n = cart pin n (n opposite n+30)
add("J3","FAMICOM60",[(pad(n), f"C{n}", "passive") for n in range(1, 61)],"CR22A60","Famicom_60pin_slot",{pad(n): v for n, v in cart.items()},"CR22A-60D-2.54DS(70)",dnp=True,
    note="HAND-SOLDER, OWNED (Leo; Sengoku). Hirose CR22A-60D-2.54DS(70); footprint from CR22 catalog D49647. Pins 31,45,46 (audio) NC")
# ---- 5 V output logic (all on +5V_CART, OE held high by pull-up until firmware enables) ----
def latch(d, q, le):
    n = {"1": OE, "10": G, "11": le, "20": VC}
    for i in range(8): n[str(2+i)] = d[i]; n[str(19-i)] = q[i]
    return n
CAD = [f"CAD{i}" for i in range(8)]; PAD = [f"PAD{i}" for i in range(8)]
add("U2","74AHCT573",ic573(),"TSSOP20","SN74AHCT573PWR",latch(CAD,[f"CA{i}" for i in range(8)],"CPU_ALE"),"SN74AHCT573PWR")
add("U3","74AHCT573",ic573(),"TSSOP20","SN74AHCT573PWR",latch(PAD,[f"PA{i}" for i in range(8)],"PPU_ALE"),"SN74AHCT573PWR")
def xcvr(dirn, a, b, oe):
    n = {"1": dirn, "10": G, "19": oe, "20": VC}
    for i in range(8): n[str(2+i)] = a[i]; n[str(18-i)] = b[i]
    return n
add("U4","74AHCT245",ic245(),"TSSOP20","74AHCT245PW",xcvr("G_RW",[f"XCD{i}" for i in range(8)],CAD,"G_M2_N"),"74AHCT245PW,118",
    note="A=cart B=MCU; DIR=R/W (H=read cart->MCU); OE_N=/M2 so enabled only in M2 high")
add("U5","74AHCT245",ic245(),"TSSOP20","74AHCT245PW",xcvr("G_WR_N",[f"XPD{i}" for i in range(8)],PAD,"PPU_DEN_N"),"74AHCT245PW,118",
    note="DIR=/WR (H=read); OE_N=PPU_DEN_N")
def buf(a, y, gnd_unused=True):
    n = {"1": OE, "19": OE, "10": G, "20": VC}
    for i in range(8):
        n[str(2+i)] = a[i] if i < len(a) else G
        if i < len(y): n[str(18-i)] = y[i]
    return n
add("U6","74AHCT541",ic541(),"TSSOP20","74AHCT541PW",buf([f"GA{8+i}" for i in range(7)]+["G_RW"],[f"CA{8+i}" for i in range(7)]+["CART_RW"]),"74AHCT541PW,118")
add("U7","74AHCT541",ic541(),"TSSOP20","74AHCT541PW",buf(["G_ROMSEL_N"]+[f"GPA{8+i}" for i in range(6)]+["G_WR_N"],["CART_ROMSEL_N"]+[f"PA{8+i}" for i in range(6)]+["CART_WR_N"]),"74AHCT541PW,118")
add("U8","74AHCT540",ic541(),"TSSOP20","SN74AHCT540PWR",buf(["G_M2_N","GPA13","G_RD"],["M2_CART","PA13_N","CART_RD_N"]),"SN74AHCT540PWR",
    note="inverting: /M2->M2, PA13->/PA13, RD->/RD; 5 unused inputs to GND")
# ---- AD series resistors (contention current limit) ----
for i in range(8):
    add(f"R{10+i}","R",TWO,"R0603","33",{"1":f"CADM{i}","2":f"CAD{i}"},"33")
    add(f"R{20+i}","R",TWO,"R0603","33",{"1":f"PADM{i}","2":f"PAD{i}"},"33")
# ---- pulls (E9: no internal pull-down; idle states) ----
rr = [30]
def res(a, b, val="10k", note=""):
    add(f"R{rr[0]}","R",TWO,"R0603",val,{"1":a,"2":b},val,note=note); rr[0] += 1
res(OE, VC, note="outputs Hi-Z until Q3 pulls low"); res("G_M2_N", V3, note="U4 off at reset"); res("PPU_DEN_N", V3, note="U5 off at reset")
res("CART_EN", G, note="cart power off at reset"); res("CART_RW", VC); res("CART_ROMSEL_N", VC); res("M2_CART", G)
res("CART_RD_N", VC); res("CART_WR_N", VC); res("IRQ_N", VC); res("CIRAM_CE_N", VC); res("CIRAM_A10", G)
res("PAD1_D", V3); res("PAD2_D", V3)
# ---- power ----
add("F1","FUSE",TWO,"F1206","500mA_PTC",{"1":VB,"2":V5},"SMD1206-050-6")
add("U9","LDO",[("1","GND","power_in"),("2","VO","power_out"),("3","VI","power_in")],"SOT223","NCP1117ST33T3G",{"1":G,"2":V3,"3":V5},"NCP1117ST33T3G")
add("C1","C",TWO,"C0805","10uF",{"1":V5,"2":G},"10uF"); add("C2","C",TWO,"C0805","10uF",{"1":V3,"2":G},"10uF")
add("C3","C",TWO,"C0805","10uF",{"1":VC,"2":G},"10uF")
add("Q1","PMOS",[("1","G","input"),("2","S","passive"),("3","D","passive")],"SOT23","AO3401A",{"1":"CART_G","2":V5,"3":VC},"AO3401A",note="cart 5 V high-side switch")
add("Q2","NMOS",[("1","G","input"),("2","S","passive"),("3","D","passive")],"SOT23","2N7002",{"1":"CART_EN","2":G,"3":"CART_G_DRV"},"2N7002")
add("Q3","NMOS",[("1","G","input"),("2","S","passive"),("3","D","passive")],"SOT23","2N7002",{"1":"CART_EN_DLY","2":G,"3":OE},"2N7002",note="enables 5 V outputs ~1 ms after cart power")
res("CART_G", V5); res("CART_EN", "CART_EN_DLY")
# Power-down guard (revc-plan 2h): U11 3.0 V open-drain detector forces CART_EN low when +3V3 sags, so the cart rail
# is switched off and the AHCT outputs go Hi-Z before IOVDD drops below the FT condition. 1k isolates GPIO43.
res("CART_EN_G", "CART_EN", "1k", note="GPIO43 -> CART_EN series (U11 may override)")
add("U11","VDET",[("1","VOUT","open_collector"),("2","VSS","power_in"),("3","VIN","power_in")],"SOT23","XC61CN3002MR-G",
    {"1":"CART_EN","2":G,"3":V3},"XC61CN3002MR-G",note="3.0 V detector, N-ch open drain (SOT-23: 1 VOUT, 2 VSS, 3 VIN)")
# P5 soft start: Q2 pulls the gate down through 1k; Cgs 100nF -> Vgs ramps with tau ~ (10k||1k)*100nF ~ 90 us
res("CART_G_DRV", "CART_G", "1k", note="gate soft-start series R")
add("C25","C",TWO,"C0603","100nF",{"1":"CART_G","2":V5},"100nF",note="Q1 gate-source soft-start C")
add("C26","C",TWO,"C0603","100nF",{"1":VC,"2":G},"100nF",note="cart-side HF bypass (with C3 10uF)")
# P3: default DIR = read (B<-A, cart->MCU) even before firmware configures the pins
res("G_RW", V3, note="U4 DIR default read"); res("G_WR_N", V3, note="U5 DIR default read")
add("C4","C",TWO,"C0603","100nF",{"1":"CART_EN_DLY","2":G},"100nF",note="RC delay for OE")
res(VC, "LED_A", "1k")
add("D1","LED",[("1","K","passive"),("2","A","passive")],"LED0603","CART_ON",{"1":G,"2":"LED_A"},"LED_G")
# ---- RP2354B support (RP2350 hardware design guide minimal design) ----
add("L1","L",TWO,"L_AOTA","3.3uH",{"1":V11,"2":"VREG_LX"},"AOTA-B201610S3R3-101-T",dnp=True,note="HAND-SOLDER (LCSC stock 0): pad1 dot = +1V1 as RP2350 Minimal R4; footprint copied from it")
add("C5","C",TWO,"C1005W","4.7uF",{"1":V3,"2":G},"4.7uF-0402",note="VREG_VIN CIN (Minimal C6)")
add("C6","C",TWO,"C1005W","4.7uF",{"1":V11,"2":G},"4.7uF-0402",note="VREG COUT (Minimal C7)")
add("C7","C",TWO,"C1005W","4.7uF",{"1":"VREG_AVDD","2":G},"4.7uF-0402",note="VREG_AVDD filter C (Minimal C9)")
add("R1","R",TWO,"R1005","33",{"1":V3,"2":"VREG_AVDD"},"33R-0402",note="VREG_AVDD RC filter (Minimal R3)")
add("Y1","XTAL",[("1","1","passive"),("2","GND","passive"),("3","3","passive"),("4","GND","passive")],"XTAL_RPI","12MHz",{"1":"XIN","2":G,"3":"XOUT","4":G},"ABM8-272-T3")
add("R2","R",TWO,"R1005","1k",{"1":"XOUT_M","2":"XOUT"},"1k-0402",note="crystal damping (HDG)")
add("C8","C",TWO,"C1005W","15pF",{"1":"XIN","2":G},"15pF-0402"); add("C9","C",TWO,"C1005W","15pF",{"1":"XOUT","2":G},"15pF-0402")
add("R3","R",TWO,"R0603","10k",{"1":"RUN","2":V3},"10k")
add("SW1","BTN",TWO,"BTN","RUN",{"1":"RUN","2":G},"TS-1187A-B-A-B")
add("R4","R",TWO,"R0603","1k",{"1":"QSPI_SS","2":"BOOT_SW"},"1k")
add("SW2","BTN",TWO,"BTN","BOOTSEL",{"1":"BOOT_SW","2":G},"TS-1187A-B-A-B")
add("J7","HDR3",conn(3),"HDR1x03","SWD",{"1":"SWCLK","2":G,"3":"SWDIO"},dnp=True)
usb = {"A1":G,"A12":G,"B1":G,"B12":G,"S1":G,"A4":VB,"A9":VB,"B4":VB,"B9":VB,"A5":"CC1","B5":"CC2","A6":"USB_DP","B6":"USB_DP","A7":"USB_DM","B7":"USB_DM"}
upins = [(k, k, "passive") for k in ["A1","A4","A5","A6","A7","A8","A9","A12","B1","B4","B5","B6","B7","B8","B9","B12","S1"]]
add("J1","USB_C",upins,"USBC","USB-C",usb,"TYPE-C-31-M-12")
add("R5","R",TWO,"R0603","5.1k",{"1":"CC1","2":G},"5.1k"); add("R6","R",TWO,"R0603","5.1k",{"1":"CC2","2":G},"5.1k")
add("R7","R",TWO,"R1005","27",{"1":"USB_DP","2":"USB_DP_C"},"27R-0402"); add("R8","R",TWO,"R1005","27",{"1":"USB_DM","2":"USB_DM_C"},"27R-0402")
# ---- CVBS 3-bit DAC + RCA ----
add("R90","R",TWO,"R0603","910",{"1":"CVBS_B0","2":"CVBS"},"910")
add("R91","R",TWO,"R0603","470",{"1":"CVBS_B1","2":"CVBS"},"470")
add("R92","R",TWO,"R0603","220",{"1":"CVBS_B2","2":"CVBS"},"220")
add("J6","RCA",[("1","SIG","passive"),("2","GND","passive")],"RCA_MJ526","RCA_CVBS",{"1":"CVBS","2":G},"MJ-526-Y",dnp=True,note="HAND-SOLDER Akizuki 112477 MJ-526-Y; footprint from Avvicon drawing MJ-526 2012/09/09")
# ---- pads (3.3 V powered; pinout is a generic header, NOT Famicom-specific) ----
for j, d in (("J4","PAD1_D"),("J5","PAD2_D")):
    add(j,"HDR7",conn(7),"HDR1x07",f"PAD_{j}",{"1":V3,"2":G,"3":"PAD_CLK","4":"PAD_LATCH","5":d},dnp=True,note="3.3 V pad only (GPIO44-47 not FT)")
# ---- I2C: U10 MCP23017 pad expander (3.3 V) + Grove J9 ----
def mcp23017():
    p = [(str(1 + i), f"GPB{i}", "bidirectional") for i in range(8)]
    p += [("9", "VDD", "power_in"), ("10", "VSS", "power_in"), ("11", "NC", "no_connect"), ("12", "SCL", "input"),
          ("13", "SDA", "bidirectional"), ("14", "NC", "no_connect"), ("15", "A0", "input"), ("16", "A1", "input"),
          ("17", "A2", "input"), ("18", "RESET_N", "input"), ("19", "INTB", "output"), ("20", "INTA", "output")]
    return p + [(str(21 + i), f"GPA{i}", "bidirectional") for i in range(8)]
# addr 0x20 (A2..A0 = 0). GPA0 CLK, GPA1 LATCH (outputs), GPA2/GPA3 = PAD1/PAD2 data (inputs, internal pull-ups on)
add("U10","MCP23017",mcp23017(),"SSOP28","MCP23017-E/SS",
    {"9":V3,"10":G,"12":"I2C_SCL","13":"I2C_SDA","15":G,"16":G,"17":G,"18":"MCP_RST_N",
     "21":"PAD_CLK","22":"PAD_LATCH","23":"PAD1_D","24":"PAD2_D"},"MCP23017-E/SS",
    note="3.3 V; pads (4021) also on 3.3 V so no level shifting is needed")
res("MCP_RST_N", V3, note="U10 reset high")
res("I2C_SDA", V3, "4.7k", note="I2C pull-up"); res("I2C_SCL", V3, "4.7k", note="I2C pull-up")
add("J9","GROVE",conn(4)+[("MP","MP","passive")],"GROVE","HY2.0-4P",{"1":G,"2":V3,"3":"I2C_SDA","4":"I2C_SCL","MP":G},"HY2.0-4P-WT",
    note="Grove I2C: 1 GND, 2 VCC 3.3V, 3 SDA, 4 SCL (Seeed order)")
# ---- decoupling: one 100 nF per IC + RP2354B supply pins ----
ci = 10
for u in ["U2","U3","U4","U5","U6","U7","U8"]:
    add(f"C{ci}","C",TWO,"C0603","100nF",{"1":VC,"2":G},"100nF",note=f"decouple {u}"); ci += 1
add("C27","C",TWO,"C0603","100nF",{"1":V3,"2":G},"100nF",note="decouple U10")
for k in range(8):
    add(f"C{ci}","C",TWO,"C0603","100nF",{"1":V3 if k < 6 else V11,"2":G},"100nF",note="decouple U1"); ci += 1
# ---- HDG audit fixes (2026-10-13): one 100 nF per supply pin (HDG 2.2.1) + 2nd 4.7 uF on VOUT at a DVDD pin (DS 6.3.8.1) ----
add("C28","C",TWO,"C0603","100nF",{"1":V3,"2":G},"100nF",note="decouple U1 IOVDD pin 24")
add("C29","C",TWO,"C1005W","100nF",{"1":V3,"2":G},"100nF-0402",note="decouple U1 IOVDD pin 29")
add("C30","C",TWO,"C1005W","4.7uF",{"1":V11,"2":G},"4.7uF-0402",note="2nd VOUT 4.7uF at DVDD pin 32, away from LX/COUT (DS 6.3.8.1)")
add("C31","C",TWO,"C0603","100nF",{"1":V3,"2":G},"100nF",note="decouple U1 ADC_AVDD pin 59")
add("C32","C",TWO,"C0603","100nF",{"1":V3,"2":G},"100nF",note="decouple U1 USB_OTP_VDD 68 + QSPI_IOVDD 69 (shared, as HDG 2.2.1)")
# ---- test points (replaces the old J8 2x20 header): THT pads on the back, no BOM part, one row for a bed-of-nails jig ----
FP["TP"] = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"   # THT: takes a 1.0 mm pin or a probe, mounted on the back
# (net, silk label) left -> right; CPU half | power | PPU half, mirrored where a counterpart exists
TPS = [(G,"GND"),(VC,"5V"),("CA0","A0"),("XCD0","D0"),("M2_CART","M2"),("CART_RW","RW"),("CART_ROMSEL_N","RS"),
       ("CPU_ALE","ALE"),("IRQ_N","IRQ"),(OE,"OE"),(V3,"3V3"),("SPARE_GP46","G46"),
       ("SPARE_GP47","G47"),(V11,"1V1"),("CVBS","VID"),("CIRAM_A10","A10"),("CIRAM_CE_N","CE"),("PPU_DEN_N","DEN"),("PPU_ALE","ALE"),
       ("CART_RD_N","RD"),("CART_WR_N","WR"),("XPD0","D0"),("PA0","A0"),(G,"GND")]
for i, (n, lbl) in enumerate(TPS):
    add(f"TP{i+1}", "TP", [("1", "1", "passive")], "TP", lbl, {"1": n}, note="test point, THT pad 2.0/1.0 mm on B side (no BOM)")
# ---- mounting holes (M3, GND pad) ----
FP["MH"] = "MountingHole:MountingHole_3.2mm_M3_Pad"
for i in range(4):
    add(f"H{i+1}", "MH", [("1", "GND", "passive")], "MH", "M3", {"1": G}, note="mounting hole")

# =====================================================================================================
# LASAGNA LITE (LASAGNA_LITE=1): same cart circuit, but U1 + its support is replaced by a Waveshare
# Core2350B module (RP2350B, 16 MB flash, 12 MHz XTAL, ME6217 3.3 V/800 mA LDO, USB 27R on-module).
# Pinout from Waveshare schematic Core2350B.pdf (P1-P4 Header 8X2) + size drawing (25.40 sq., 10x10 grid,
# 2.54 mm, two-deep ring) on the Core2350B0 wiki. Cheapest build: everything not needed to dump is dropped.
# =====================================================================================================
import os as _os
LITE = _os.environ.get("LASAGNA_LITE") == "1"
def core2350b_pins():
    """(pad, name, grid col, grid row) for the 64 module pads; pad = header*100 + pin (e.g. 201 = P2 pin 1)."""
    out = []
    def gpio_hdr(h, base):
        for p in range(1, 17):
            if p == 1: nm = "GND"
            elif p == 2: nm = f"GPIO{base}"
            elif p % 2 == 0: nm = f"GPIO{base + p - 3}"
            else: nm = f"GPIO{base + p - 1}"
            yield p, nm
    P2 = {1:"GND",2:"GPIO45",3:"GPIO47",4:"GPIO46",5:"BOOTSEL",6:"SWDIO",7:"USBD_N",8:"GND",9:"USBD_P",10:"SWCLK",
          11:"RUN",12:"ADC_VREF",13:"3V3_EN",14:"GND",15:"VBUS",16:"3V3"}
    for p, nm in gpio_hdr(1, 0):  out.append((100 + p, nm, 0 if p % 2 else 1, (p - 1) // 2 if p % 2 else (p - 2) // 2))
    for p in range(1, 17):         out.append((200 + p, P2[p], 9 - ((p - 1) // 2 if p % 2 else (p - 2) // 2), 0 if p % 2 else 1))
    for p, nm in gpio_hdr(3, 15): out.append((300 + p, nm, (p - 1) // 2 if p % 2 else (p - 2) // 2, 9 if p % 2 else 8))
    for p, nm in gpio_hdr(4, 30): out.append((400 + p, nm, 9 if p % 2 else 8, 9 - ((p - 1) // 2 if p % 2 else (p - 2) // 2)))
    assert len({(c, r) for _, _, c, r in out}) == 64 and len({n for _, n, _, _ in out if n.startswith("GPIO")}) == 48
    return out
LITE_DROP = {"U1", "L1", "C5", "C6", "C7", "C8", "C9", "R1", "R2", "Y1", "R3", "R4", "R7", "R8", "U9", "C2",
             "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24", "C28", "C29", "C30", "C31", "C32",
             "J6", "R90", "R91", "R92", "J9", "U10", "R51", "R52", "R53", "C27", "J4", "J5", "R42", "R43", "J7"}
LITE_DROP2 = {"F1", "SW1", "SW2", "U11", "Q1", "Q2", "Q3", "R44", "R45", "R46", "R47", "C25", "C4", "C3", "C26",
              "R33", "R34", "R35", "R36", "R37", "R38", "R40", "R41", "R48", "R49"}
LITE_NC_GPIO = set()     # all 48 used: GPIO40-42 CVBS DAC, 44/45 I2C (DNP features), 46/47 expansion J10 (47 = PSRAM CS on B1/B2!)
LITE_DNP_KEEP = {"J6", "R90", "R91", "R92", "J9", "U10", "R51", "R52", "R53", "C27", "J4", "J5", "R42", "R43", "SW1", "SW2", "F1"}
# ---- WeAct Studio RP2350B Core Board V1.0 (verified against HDK/RP2350B_SCH.pdf H1/H2 + RP2350B_PINOUT.png) ----
# Board 41.148 (x, across the headers) x 41.402 (y) mm with the USB-C edge toward +y (board front). Rows 38.10 apart.
WEACT_W, WEACT_L = 41.148, 41.402
WEACT_EDGE = 1.778          # module USB edge -> pin 1/2 row; far edge 4.064 beyond pin 29/30 row (dimension drawing)
def weact_h1(p):
    return {1: "VBUS", 2: "5V", 3: "GND", 4: "GND", 5: "VREF"}.get(p) or f"GPIO{p - 6}"
def weact_h2(p):
    if p <= 8: return {1: "GND", 2: "GND", 3: "3V3_EN", 4: "GND", 5: "3V3", 6: "3V3", 7: "GPIO47", 8: "RUN"}[p]
    return f"GPIO{54 - p}" if p % 2 else f"GPIO{56 - p}"
def weact_pins():
    """(pad, name, x, y) in footprint coords (mm, origin = module centre, +y = USB edge). H1 = right, H2 = left (top view)."""
    out = []
    y1 = WEACT_L / 2 - WEACT_EDGE
    for p in range(1, 31):
        y = y1 - ((p - 1) // 2) * 2.54
        out.append((str(100 + p), weact_h1(p), 19.05 if p % 2 else 16.51, y))      # H1 odd = outer row
        out.append((str(200 + p), weact_h2(p), -16.51 if p % 2 else -19.05, y))    # H2 even = outer row
    assert len({n for _, n, _, _ in out if n.startswith("GPIO")}) == 48
    return out
# GPIO map for the WeAct port (firmware swap approved 2026-10-17). PIO windows: PPU 0-31, CPU 16-47.
GP_LITE = {i: f"PADM{i}" for i in range(8)} | {8 + i: f"GPA{8 + i}" for i in range(6)}
GP_LITE |= {14: "PPU_DEN_N", 15: "G_RD", 16: "G_WR_N", 17: "PPU_ALE",
            18: "CVBS_B0", 19: "CVBS_B1", 20: "CVBS_B2", 21: "IRQ_N", 22: "CIRAM_CE_N", 23: "OUT_OE_N", 24: "CIRAM_A10"}
GP_LITE |= {25 + i: f"CADM{i}" for i in range(8)} | {33 + i: f"GA{8 + i}" for i in range(7)}
GP_LITE |= {40: "G_RW", 41: "G_ROMSEL_N", 42: "G_M2_N", 43: "CPU_ALE", 44: "I2C_SDA", 45: "I2C_SCL", 46: "SPARE_GP46", 47: "SPARE_GP47"}
assert sorted(GP_LITE) == list(range(48)) and sorted(GP_LITE.values()) == sorted({"CART_EN_G": "OUT_OE_N"}.get(v, v) for v in gp.values())
PPU_GPIO, CPU_GPIO = range(0, 18), range(25, 44)
WEACT_DROP = {"J1", "R5", "R6", "U12", "SW1", "SW2"}
def apply_lite():
    global COMPS, TPS
    led = [c["ref"] for c in COMPS if set(c["nets"].values()) & {"LED_A"}]          # D1 + its 1k: module LED is enough
    keep = [c for c in COMPS if c["ref"] not in (LITE_DROP - LITE_DNP_KEEP) | set(led)]
    FP["CORE2350B"] = "NESPICO_RevC:Waveshare_Core2350B"
    pins, nets = [], {}
    other = {"GND": G, "BOOTSEL": "BOOT_SW", "USBD_N": "USB_DM", "USBD_P": "USB_DP", "RUN": "RUN", "VBUS": V5, "3V3": V3,
             "SWDIO": "SWDIO", "SWCLK": "SWCLK"}
    ptype = {"GND": "power_in", "VBUS": "power_in", "3V3": "power_out"}
    for pad, nm, _, _ in core2350b_pins():
        pins.append((str(pad), nm, ptype.get(nm, "bidirectional")))
        if nm.startswith("GPIO"):
            g = int(nm[4:])
            if g not in LITE_NC_GPIO: nets[str(pad)] = gp[g]
        elif nm in other: nets[str(pad)] = other[nm]
    # WeAct port (2026-10-17): the Waveshare pin list above is superseded by the WeAct RP2350B Core Board (weact_pins()).
    nets = {}; pins = []
    wother = {"GND": G, "3V3": V3, "VBUS": "VBUS_IN", "RUN": "RUN"}   # H1-2 (+5V after diode), 3V3_EN, VREF: NC; RUN -> J12 (DNP)
    wtype = {"GND": "power_in", "VBUS": "power_out"}
    for pad, nm, _, _ in sorted(weact_pins(), key=lambda r: int(r[0])):    # symbol: H1 left, H2 right
        t = wtype.get(nm, "power_out" if pad == "205" else ("passive" if nm == "3V3" else
             ("passive" if nm in ("5V", "VREF", "3V3_EN", "RUN") else "bidirectional")))
        pins.append((pad, nm, t))
        if nm.startswith("GPIO"): nets[pad] = GP_LITE[int(nm[4:])]
        elif nm in wother: nets[pad] = wother[nm]
    m = dict(ref="U1", sym="WEACT_RP2350B", pins=pins, fp="NESPICO_RevC:WeAct_RP2350B_CoreBoard", value="WeAct RP2350B",
             mpn="WeAct RP2350B Core Board V1.0", nets=nets, dnp=True,
             note="WeAct Studio RP2350B Core Board V1.0 (16 MB flash). H1 101-130, H2 201-230. VBUS (H1-1, raw USB) feeds F1; "
                  "H1-2 (+5V after diode), H2-3 3V3_EN and H1-5 VREF are NC; H2-8 RUN goes to the DNP reset header J12. LIFT module R16 (GP23 KEY) and never fit "
                  "the PSRAM/flash2 footprint U7 (CS = GP0). GP25 drives the module LED via 5.1k (CADM0: harmless).")
    for c in keep:
        if c["ref"] == "SW2": c["nets"] = {"1": "BOOT_SW", "2": G}                 # module has the 1k QSPI_SS series R
        if c["ref"] in ("SW1", "SW2"): c["dnp"] = True; c["note"] = "OPTIONAL: blank flash boots to USB BOOTSEL by itself"
    # --- Lite cost-down (<=3000 JPY): module's own FPC USB adapter supplies USB+5V+RUN/BOOT, so no USB-C/CC/PTC/buttons;
    # cart rail = +5V_LOGIC direct (no supervisor/high-side switch: plug carts with power OFF); GPIO43 drives OE# itself,
    # pulled up to 3V3 (AHCT VIH 2.0 V) so outputs stay Hi-Z through reset; only the pulls that matter at reset stay.
    keep = [c for c in keep if c["ref"] not in LITE_DROP2 - LITE_DNP_KEEP]
    ren = {"+5V_CART": V5, "CART_EN_G": "OUT_OE_N"}
    for c in keep:
        c["nets"] = {k: ren.get(v, v) for k, v in c["nets"].items()}
        if c["ref"] == "R39": c["nets"] = {"1": "IRQ_N", "2": V3}; c["note"] = "IRQ_N pull-up to 3V3 (cart /IRQ is open-drain; no 5V on GPIO21)"
        if c["ref"] == "R30": c["nets"] = {"1": "OUT_OE_N", "2": V3}; c["note"] = "OE# pull-up to 3V3: buffers Hi-Z until FW drives GPIO23 low"
    # USB-C = Akizuki 115426 AE-USB2.0-TYPE-C-5077CR DIP breakout (no CC resistors on it -> R5/R6 5.1k here); VBUS = +5V_LOGIC
    # (module VBUS + cart rail, no PTC). Module FPC/kit adapter not needed; BOOTSEL/RUN on test pads (short to GND).
    for c in keep:
        if c["ref"] == "J1":
            FP["AKI_USBC"] = "NESPICO_RevC:Akizuki_AE-USB2.0-TYPE-C-5077CR"
            c.update(sym="AKI_USBC", fp=FP["AKI_USBC"], value="AE-USB2.0-TYPE-C-5077CR", mpn="Akizuki 115426", dnp=True,
                     pins=[("1", "VBUS", "passive"), ("2", "D-", "bidirectional"), ("3", "D+", "bidirectional"), ("4", "GND", "power_in"),
                           ("5", "CC1", "passive"), ("6", "CC2", "passive"), ("7", "GND", "power_in")],
                     nets={"1": V5, "2": "USB_DM", "3": "USB_DP", "4": G, "5": "CC1", "6": "CC2", "7": G},
                     note="Akizuki 115426 (180 JPY) USB-C DIP breakout on a 1x7 2.54 header; mouth flush with the left edge")
    m["nets"] = {k: ren.get(v, v) for k, v in m["nets"].items()}
    # VBUS backfeed guard: J1 VBUS -> D2 SS34 Schottky -> +5V_LOGIC (module VBUS + cart). JP1 (NO solder jumper) bypasses D2.
    # Stops a module-FPC / external 5V on +5V_LOGIC from feeding back into the J1 host port.
    for c in keep:
        if c["ref"] == "J1": c["nets"]["1"] = "VBUS_IN"
    FP["D_SMA"] = "Diode_SMD:D_SMA"; FP["SJ2"] = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
    LCSC["SS34"] = ("C8678", "verified JLC API 2026-10-13: MDD SS34 SMA, Basic, stock ~4.1M, MOQ 20, $0.035")
    keep.append(dict(ref="D2", sym="D_SCHOTTKY", pins=[("1", "K", "passive"), ("2", "A", "passive")], fp=FP["D_SMA"], value="SS34",
                     mpn="SS34", nets={"1": V5, "2": "VBUS_IN"}, dnp=True, nofit=True,
                     note="DNP option: VBUS series Schottky for FPC-backfeed protection; fit D2 AND cut JP1 (default bridged)"))
    keep.append(dict(ref="JP1", sym="SJ", pins=[("1", "1", "passive"), ("2", "2", "passive")], fp="Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", value="CUT=USE D",
                     mpn="", nets={"1": "VBUS_IN", "2": V5}, dnp=True, note="bridged by default (VBUS direct); cut it when D2 is fitted"))
    # Full-version features kept as DNP footprints (populate later to enable). Nothing here changes the fitted BOM.
    FP["F0805"] = "Fuse:Fuse_0805_2012Metric"; FP["SJ2B"] = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
    FP["SOT236"] = "Package_TO_SOT_SMD:SOT-23-6"; FP["HDR1x05"] = "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
    for c in keep:
        if c["ref"] in LITE_DNP_KEEP:
            c["dnp"] = True; c["nofit"] = True; c["note"] = "DNP (Lite option). " + c.get("note", "")
        if c["ref"] == "F1":       # fitted (Leo 2026-10-14): hold 500 mA / trip 1 A, 150-850 mOhm
            c.update(fp=FP["F0805"], value="PTC 0805 500mA", mpn="SMD0805-050", nets={"1": "VBUS_IN", "2": "VBUS_F"}, dnp=False, nofit=False,
                     note="TECHFUSE SMD0805-050 PTC, hold 0.5 A / trip 1 A, Rmin 150 mOhm; JP2 (open) bypasses it")
    LCSC["SMD0805-050"] = ("C66452", "verified JLC API/LCSC 2026-10-14: TECHFUSE SMD0805-050, 500 mA hold, 1 A trip, 6 V, stock ~11k, MOQ 10, $0.037")
    LCSC["USBLC6-2SC6"] = ("C2687116", "verified JLC API/LCSC 2026-10-14: UMW USBLC6-2SC6 SOT-23-6, stock ~63k, MOQ 10, $0.048 (no Basic USBLC6)")
    for c in keep:
        if c["ref"] in ("D2", "JP1"): c["nets"] = {k: ("VBUS_F" if v == "VBUS_IN" else v) for k, v in c["nets"].items()}
    keep.append(dict(ref="JP2", sym="SJ", pins=[("1", "1", "passive"), ("2", "2", "passive")], fp=FP["SJ2B"], value="SHORT=BYPASS F", mpn="",
                     nets={"1": "VBUS_IN", "2": "VBUS_F"}, dnp=True, note="normally open; solder-short to bypass PTC F1"))
    keep.append(dict(ref="U12", sym="USBLC6", pins=[("1", "IO1", "passive"), ("2", "GND", "passive"), ("3", "IO2", "passive"),
                     ("4", "IO2", "passive"), ("5", "VBUS", "passive"), ("6", "IO1", "passive")], fp=FP["SOT236"], value="USBLC6-2SC6",
                     mpn="USBLC6-2SC6", nets={"1": "USB_DM", "6": "USB_DM", "3": "USB_DP", "4": "USB_DP", "2": G, "5": "VBUS_IN"}, dnp=False,
                     note="USB D+/D- ESD clamp (UMW USBLC6-2SC6, C2687116); shunt-only"))
    keep.append(dict(ref="J10", sym="HDR5", pins=[(str(i), str(i), "passive") for i in range(1, 6)], fp=FP["HDR1x05"], value="EXP",
                     mpn="", nets={"1": V3, "2": "SPARE_GP46", "3": "SPARE_GP47", "4": G, "5": V5}, dnp=True, nofit=True,
                     note="expansion: 3V3, GPIO46, GPIO47, GND, 5V. GPIO46/47 are 3.3 V ADC pins, NOT 5 V tolerant"))
    # J12 (DNP, 2026-10-17): external reset button / case switch header, RUN (module H2-8, pulled up on the module) to GND
    keep.append(dict(ref="J12", sym="HDR2", pins=[("1", "1", "passive"), ("2", "2", "passive")], fp=FP["HDR1x02"], value="RST",
                     mpn="", nets={"1": "RUN", "2": G}, dnp=True, nofit=True,
                     note="optional external RESET: short RUN to GND (module also has its own RST/BOOT buttons)"))
    # Grove J9 -> Seeed standard pin order (Leo 2026-10-14): 1 SCL (yellow), 2 SDA (white), 3 VCC 3V3 (red), 4 GND (black)
    for c in keep:
        if c["ref"] == "J9":
            c["nets"] = {"1": "I2C_SCL", "2": "I2C_SDA", "3": V3, "4": G, "MP": G}
            c["note"] = "DNP (Lite option). Grove I2C, Seeed standard: 1 SCL (GPIO45), 2 SDA (GPIO44), 3 VCC 3V3, 4 GND"
    # DNP audio out (Leo 2026-10-14): GPIO46 PWM -> R60 1k -> AUD_F (C60 10nF to GND: RC low-pass fc = 15.9 kHz)
    # -> C61 10uF DC block -> AUD_OUT -> J11 RCA (same Akizuki 112477 MJ-526-Y as J6), R61 10k bleed to GND.
    # Optional cart expansion audio (NESdev cartridge connector, Famicom 60-pin): pin 45 = "Audio from 2A03" (console -> cart),
    # pin 46 = "Audio to RF" (cart -> console). Pin 45 is NC (former R63 GP46 -> pin 45 removed:
    # no GPIO40-47 path to the cart). R62 1k mixes cart pin 46 into AUD_F. GPIO46 stays on J10 pin 2 and TP G46.
    LCSC["10nF"] = ("C57112", "verified JLC part page 2026-10-14: FH 0603B103K500NT 10nF 50V X7R 0603, JLC Basic")
    two = [("1", "1", "passive"), ("2", "2", "passive")]
    for ref, sym, fp, val, nets, note in (
        ("R60", "R", "R0603", "1k", {"1": "SPARE_GP46", "2": "AUD_F"}, "audio PWM series R (RC low-pass with C60, fc 15.9 kHz)"),
        ("C60", "C", "C0603", "10nF", {"1": "AUD_F", "2": G}, "audio RC low-pass C"),
        ("C61", "C", "C0805", "10uF", {"1": "AUD_F", "2": "AUD_OUT"}, "audio DC-block C (pin 1 = filter side)"),
        ("R61", "R", "R0603", "10k", {"1": "AUD_OUT", "2": G}, "audio output bleed to GND (keeps C61 output at 0 V DC)"),
        ("R62", "R", "R0603", "1k", {"1": "CART_AUD_OUT", "2": "AUD_F"}, "mix cart expansion audio (cart pin 46, Audio to RF) into AUD_F")):
        # R63 (GP46 -> cart pin 45) deleted 2026-10-17: GPIO40-47 must never reach the cart. Cart pin 45 is NC again.
        keep.append(dict(ref=ref, sym=sym, pins=two, fp=FP[fp], value=val, mpn=val, nets=nets, dnp=True, nofit=True,
                         note="DNP (Lite option: audio). " + note))
    keep.append(dict(ref="J11", sym="RCA", pins=[("1", "SIG", "passive"), ("2", "GND", "passive")], fp=FP["RCA_MJ526"], value="RCA_AUDIO",
                     mpn="MJ-526-Y", nets={"1": "AUD_OUT", "2": G}, dnp=True, nofit=True,
                     note="DNP (Lite option: audio). HAND-SOLDER Akizuki 112477 MJ-526-Y (same as J6)"))
    for c in keep:
        if c["ref"] == "J3":
            c["nets"] = dict(c["nets"], **{"46": "CART_AUD_OUT"})
            c["note"] = c["note"].replace("Pins 31,45,46 (audio) NC", "Pins 31, 45 NC; 46 = audio from cart (R62, DNP)")
    # 33R series: 4x 4-element arrays (UniOhm 4D03WGJ0330T5E, LCSC C25508), each = 4 adjacent bus bits; element k = pins k / 9-k
    keep = [c for c in keep if not (c["ref"][0] == "R" and c["ref"][1:].isdigit() and (10 <= int(c["ref"][1:]) <= 17 or 20 <= int(c["ref"][1:]) <= 27))]
    FP["RARR4"] = "Resistor_SMD:R_Array_Convex_4x0603"
    LCSC["4D03WGJ0330T5E"] = ("C25508", "verified LCSC page 2026-10-13: 4D03WGJ0330T5E 33R x4 0603 convex, stock ~110k, MOQ 50, $0.013")
    rpins = [(str(i), str(i), "passive") for i in range(1, 9)]
    for k, (bus, b0) in enumerate((("CADM", 0), ("CADM", 4), ("PADM", 0), ("PADM", 4))):
        nets = {}
        for e in range(4):
            # MCU side pins 1-4, bus side 8-5. WeAct layout: element e carries bit b0+3-e so pin 4 (lowest bit) lines up
            # with the header pin it faces (RN1/RN2 at 180 deg left of H2, RN3/RN4 at 0 deg right of H1).
            nets[str(e + 1)] = f"{bus}{b0 + 3 - e}"; nets[str(8 - e)] = f"{bus[:-1]}{b0 + 3 - e}"
        keep.append(dict(ref=f"RN{k + 1}", sym="RPACK4", pins=rpins, fp=FP["RARR4"], value="33x4", mpn="4D03WGJ0330T5E", nets=nets,
                         dnp=False, note=f"33R x4 series, {bus}{b0}-{b0 + 3}"))
    # Waveshare photo shows RP2350B0A2 (E9 present): R41 fitted as 5.1k (<= 8.2k per datasheet D.5.1).
    # Kept fitted: R30 OE# pull-up (buffers Hi-Z through reset), R31/R32 (U4/U5 off at reset), R39 IRQ_N (open-drain cart IRQ).
    for c in COMPS:
        if c["ref"] == "R41":     # CIRAM_A10 pull-down on a GPIO input: E9-only
            c = dict(c, nets={k: ren.get(v, v) for k, v in c["nets"].items()}, value="5.1k", mpn="5.1k", dnp=False, nofit=False,
                     note="RP2350-E9 (A2): external pull-down <= 8.2k on CIRAM_A10 (GPIO24). 5.1k (C23186)")
            keep.append(c)
    TPS = [(ren.get(n, n), l) for n, l in TPS]
    COMPS = [m] + [c for c in keep if not c["ref"].startswith("TP")]
    dead = {V11, "CVBS"} if not LITE else {V11, "CVBS"}
    TPS = [t for t in TPS if t[0] not in dead]
    # WeAct: module has BOOT/RST buttons, own USB-C (CC, ESD); SWD/BOOT/RUN test points dropped, GND TP restored
    COMPS = [c for c in COMPS if c["ref"] not in WEACT_DROP]
    # Pin swap (Lite only, firmware-invisible): the 573 latches are bit-agnostic, so D/Q pair j carries bit 7-j. With the
    # latches rotated 90 deg this puts CA7..CA0 / PA7..PA0 left->right like the cart pins and the CAD/PAD order like the 245s.
    for c in COMPS:
        if c["ref"] in ("U2", "U3"):
            n = dict(c["nets"]); d = [n[str(2 + i)] for i in range(8)]; qq = [n[str(19 - i)] for i in range(8)]
            for i in range(8): n[str(2 + i)] = d[7 - i]; n[str(19 - i)] = qq[7 - i]
            c["nets"] = n; c["note"] = (c.get("note", "") + " Lite pin swap: D/Q pair j = bit 7-j (latch is bit-agnostic).").strip()   # BOOT/RUN: short to GND (one GND TP fewer)   # BOOT/RUN: short to GND      # SWD on the TP row (no J7 header)
    for i, (n, lbl) in enumerate(TPS):
        COMPS.append(dict(ref=f"TP{i+1}", sym="TP", pins=[("1", "1", "passive")], fp=FP["TP"], value=lbl, mpn="", nets={"1": n}, dnp=False,
                          note="test point, THT pad 2.0/1.0 mm on B side (no BOM)"))
    hs = [c for c in COMPS if c["ref"].startswith("H")]; COMPS = [c for c in COMPS if not c["ref"].startswith("H")] + hs
if LITE:
    apply_lite()

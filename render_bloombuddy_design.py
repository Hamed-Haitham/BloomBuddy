from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse, Polygon, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "design-renders"
OUT.mkdir(exist_ok=True)
PCB_PATH = ROOT / "BloomBuddy-Rev-A.kicad_pcb"

BG = "#07131a"
PANEL = "#0c2028"
PANEL2 = "#102d34"
INK = "#e6f7ed"
MUTED = "#8eb2ad"
MINT = "#8ff0ba"
TEAL = "#39c6b0"
GOLD = "#ffd166"
CORAL = "#ff7b72"
PURPLE = "#b79cff"
BLUE = "#6bc5ff"
COPPER = "#d18a4b"
BOARD = "#143d3e"
BOARD_EDGE = "#7ee2be"


def style_ax(ax, title, subtitle=""):
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.text(0.035, 0.94, title, transform=ax.transAxes, color=INK, fontsize=22,
            fontweight="bold", va="top", family="DejaVu Sans")
    if subtitle:
        ax.text(0.036, 0.905, subtitle, transform=ax.transAxes, color=MUTED, fontsize=9.5,
                va="top", family="DejaVu Sans")
    ax.text(0.965, 0.945, "BLOOMBUDDY / REV A", transform=ax.transAxes, color=TEAL,
            fontsize=8, ha="right", va="top", family="DejaVu Sans", fontweight="bold")


def save(fig, name):
    fig.savefig(OUT / name, dpi=180, facecolor=BG, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def rounded(ax, xy, w, h, fc=PANEL, ec="#28535b", radius=0.025, lw=1.2, alpha=1):
    patch = FancyBboxPatch(xy, w, h, boxstyle=f"round,pad=0.012,rounding_size={radius}",
                           facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha)
    ax.add_patch(patch)
    return patch


def board_shape(ax, x=0, y=0, w=1, h=1, angle=0, fc=BOARD, ec=BOARD_EDGE, lw=2.0):
    # A rounded PCB with clipped-corner silhouette.
    pts = np.array([[x+0.05*w,y], [x+0.95*w,y], [x+w,y+0.05*h], [x+w,y+0.95*h],
                    [x+0.95*w,y+h], [x+0.05*w,y+h], [x,y+0.95*h], [x,y+0.05*h]])
    if angle:
        c = np.array([x+w/2,y+h/2])
        r = math.radians(angle)
        R = np.array([[math.cos(r),-math.sin(r)],[math.sin(r),math.cos(r)]])
        pts = (pts-c)@R.T+c
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))
    return pts


def component(ax, x, y, w=0.06, h=0.035, label=None, color=GOLD, z=6, rotate=0, dark=False):
    fc = "#172a2e" if dark else color
    ec = "#b9f3d0" if dark else "#fff0af"
    r = Rectangle((x-w/2,y-h/2), w, h, angle=rotate, facecolor=fc, edgecolor=ec,
                  linewidth=0.7, zorder=z)
    ax.add_patch(r)
    if label:
        ax.text(x, y+h*0.95, label, color=INK if dark else "#fff3c2", fontsize=5.5,
                ha="center", va="bottom", zorder=z+1)


def parse_pcb():
    text = PCB_PATH.read_text()
    fp = []
    for m in re.finditer(r'\(footprint "([^"]+)".*?(?=\n  \(footprint |\n  \(gr_|\n  \(segment |\n\))', text, re.S):
        b = m.group(0)
        at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?', b)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        if at and ref:
            fp.append({"ref": ref.group(1), "name": m.group(1), "x": float(at.group(1)), "y": float(at.group(2)), "rot": float(at.group(3) or 0)})
    seg = []
    for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\).*?\(layer "([^"]+)"\)', text):
        seg.append(tuple(map(float, m.groups()[:4])) + (m.group(5),))
    return fp, seg


FP, SEG = parse_pcb()
MINX, MAXX, MINY, MAXY = 74, 130, 138, 209

def map_board(x, y, x0=0.12, y0=0.16, w=0.76, h=0.70):
    return x0 + (x-MINX)/(MAXX-MINX)*w, y0 + (y-MINY)/(MAXY-MINY)*h


def draw_pcb(ax, x0=0.12, y0=0.16, w=0.76, h=0.70, labels=True, traces=True, z=1):
    board_shape(ax, x0, y0, w, h, fc=BOARD, ec=BOARD_EDGE, lw=2.0)
    # copper pours / traces
    if traces:
        for x1,y1,x2,y2,layer in SEG[::2]:
            a = map_board(x1,y1,x0,y0,w,h); b = map_board(x2,y2,x0,y0,w,h)
            c = COPPER if layer == "F.Cu" else "#6d5b40"
            ax.plot([a[0],b[0]],[a[1],b[1]], color=c, alpha=0.38, linewidth=0.65, zorder=z+1)
    for item in FP:
        x,y = map_board(item["x"],item["y"],x0,y0,w,h)
        name=item["name"]
        if "ESP32" in name: component(ax,x,y,.14,.06,item["ref"],PURPLE,dark=True)
        elif "USB" in name or "Terminal" in name: component(ax,x,y,.08,.055,item["ref"],BLUE,dark=True)
        elif "QFN" in name or "SOT" in name: component(ax,x,y,.06,.05,item["ref"],CORAL)
        elif "PinHeader" in name or "Connector" in name: component(ax,x,y,.035,.075,item["ref"],MINT,dark=True)
        elif "LED" in name: component(ax,x,y,.032,.028,item["ref"],CORAL)
        elif "SW_" in name or "OS102" in name: component(ax,x,y,.055,.04,item["ref"],GOLD)
        else: component(ax,x,y,.025,.018,item["ref"],GOLD)
    if labels:
        ax.text(x0+0.03, y0+h-0.03, "BLOOMBUDDY / SENSOR HUB", color=MINT, fontsize=8, fontweight="bold", zorder=10)
        ax.text(x0+w-0.025, y0+0.025, "REV A   ·   ENIG   ·   1.6 mm FR4", color=MUTED, fontsize=5.6, ha="right", zorder=10)


def render_hero():
    fig, ax = plt.subplots(figsize=(14,8), dpi=180)
    style_ax(ax, "BloomBuddy — full design render", "A compact plant-care companion: controller, power, sensing, audio, and enclosure in one system")
    rounded(ax,(0.035,0.08),0.93,0.79,fc="#091b22",ec="#173d45",radius=.018,lw=1.0)
    # enclosure shadow and body
    rounded(ax,(0.09,0.19),0.42,0.46,fc="#102832",ec="#3b6870",radius=.04,lw=1.3)
    # enclosure front panel
    rounded(ax,(0.135,0.245),0.33,0.30,fc="#17363b",ec="#6bc5a9",radius=.03,lw=1.5)
    ax.add_patch(Circle((0.30,0.395),0.103,facecolor="#0b1d24",edgecolor=MINT,lw=2))
    ax.add_patch(Circle((0.30,0.395),0.080,facecolor="#153e3a",edgecolor="#4c9f89",lw=1))
    # flower/plant icon
    for ang in np.linspace(0, 2*np.pi, 6, endpoint=False):
        cx=0.30+0.048*np.cos(ang); cy=0.395+0.048*np.sin(ang)
        ax.add_patch(Ellipse((cx,cy),0.035,0.06,angle=np.degrees(ang),fc="#6fd59d",ec="#b0f4c0",lw=.5))
    ax.add_patch(Circle((0.30,0.395),0.022,fc=GOLD,ec="#fff1b0",lw=.8))
    ax.text(0.30,0.285,"BLOOMBUDDY",ha="center",color=INK,fontsize=10,fontweight="bold")
    ax.text(0.30,0.268,"GROW WITH A LITTLE HELP",ha="center",color=MUTED,fontsize=5.5)
    # sensor cable
    ax.plot([0.47,0.56,0.60],[0.34,0.29,0.29],color=MINT,lw=2)
    ax.add_patch(Circle((0.62,0.29),0.035,fc="#254f45",ec=MINT,lw=1.5))
    ax.text(0.62,0.235,"SOIL PROBE",ha="center",color=MUTED,fontsize=7)
    # board floating
    board_shape(ax,0.61,0.18,0.27,0.48,fc="#174d4d",ec=MINT,lw=2.2)
    for x,y in [(0.665,.29),(.74,.31),(.80,.36),(.70,.47),(.80,.56),(.68,.61)]:
        component(ax,x,y,.045,.026,None,GOLD)
    rounded(ax,(0.685,.49),.115,.055,fc="#132431",ec=PURPLE,radius=.008,lw=1)
    ax.text(.7425,.518,"ESP32",ha="center",va="center",color=PURPLE,fontsize=7,fontweight="bold")
    rounded(ax,(.807,.235),.048,.09,fc="#132431",ec=BLUE,radius=.008,lw=1)
    ax.text(.831,.28,"USB",ha="center",va="center",rotation=90,color=BLUE,fontsize=6,fontweight="bold")
    ax.text(.745,.205,"REV A CONTROL BOARD",ha="center",color=INK,fontsize=7,fontweight="bold")
    # battery + signal cards
    rounded(ax,(0.56,0.70),0.35,0.11,fc="#112f36",ec="#2f6f68",radius=.02)
    ax.text(.585,.77,"SYSTEM STACK",color=MINT,fontsize=8,fontweight="bold")
    ax.text(.585,.735,"K10 host  ·  LiPo power  ·  moisture probe  ·  status LEDs",color=INK,fontsize=7)
    # callouts
    for y,lab,desc,col in [(0.66,"01  CONTROLLER","ESP32 / K10 compute core",PURPLE),(0.56,"02  POWER","USB-C, LiPo, charge + protection",BLUE),(0.46,"03  FEEDBACK","RGB/status LEDs + speaker path",CORAL)]:
        ax.plot([.54,.61],[y,y],color=col,lw=1.2)
        ax.text(.535,y+.012,lab,ha="right",color=col,fontsize=7,fontweight="bold")
        ax.text(.615,y+.012,desc,color=INK,fontsize=7)
    ax.text(.06,.105,"DESIGN INTENT",color=GOLD,fontsize=7,fontweight="bold")
    ax.text(.06,.083,"Soft, friendly enclosure language around an engineered core — readable at a glance, serviceable on the bench.",color=MUTED,fontsize=7.5)
    save(fig,"01_full_assembly_render.png")


def render_pcb():
    fig, ax = plt.subplots(figsize=(10,10), dpi=180)
    style_ax(ax, "BloomBuddy — PCB layout", "Actual Rev A KiCad geometry with routed nets, footprints, headers, power, and controller zones")
    draw_pcb(ax,0.13,0.12,.72,.76)
    # side legend
    rounded(ax,(.87,.18),.095,.53,fc=PANEL,ec="#28535b",radius=.02)
    ax.text(.885,.67,"LAYER KEY",color=MINT,fontsize=7,fontweight="bold")
    for i,(c,t) in enumerate([(PURPLE,"ESP32 core"),(BLUE,"Power / USB"),(CORAL,"IC / LED"),(GOLD,"Passives"),(MINT,"Headers")]):
        yy=.62-i*.075; ax.add_patch(Rectangle((.885,yy),.025,.025,fc=c,ec="white",lw=.4)); ax.text(.92,yy+.012,t,color=INK,fontsize=6.4,va="center")
    ax.text(.885,.24,"544",color=GOLD,fontsize=17,fontweight="bold"); ax.text(.885,.215,"routed segments",color=MUTED,fontsize=6)
    ax.text(.885,.365,"35",color=TEAL,fontsize=17,fontweight="bold"); ax.text(.885,.34,"vias",color=MUTED,fontsize=6)
    ax.text(.13,.065,"BOARD ENVELOPE  ·  sensor I/O at left  ·  USB / power at right  ·  audio + status path across lower rail",color=MUTED,fontsize=7)
    save(fig,"02_pcb_layout_render.png")


def render_schematic():
    fig, ax = plt.subplots(figsize=(14,8), dpi=180)
    style_ax(ax, "BloomBuddy — system schematic", "Functional architecture reconstructed from the Rev A net names and component groups")
    rounded(ax,(.04,.10),.92,.75,fc="#091b22",ec="#173d45",radius=.02)
    # vertical lanes
    lanes=[(.075,.76,"POWER",BLUE),(.27,.76,"COMPUTE",PURPLE),(.48,.76,"SENSING",MINT),(.68,.76,"FEEDBACK",CORAL),(.85,.76,"EXPANSION",GOLD)]
    for x,y,name,c in lanes:
        ax.text(x,y,name,color=c,fontsize=8,fontweight="bold",ha="center")
    def block(x,y,w,h,title,detail,c):
        rounded(ax,(x,y),w,h,fc=PANEL2,ec=c,radius=.015,lw=1.5)
        ax.text(x+w/2,y+h*.62,title,color=INK,fontsize=9,fontweight="bold",ha="center")
        ax.text(x+w/2,y+h*.30,detail,color=MUTED,fontsize=6.3,ha="center",wrap=True)
    block(.055,.51,.16,.14,"USB-C / LiPo","USB_VBUS · BAT_POS\nCHG_SYS · SYS_ENABLE",BLUE)
    block(.27,.49,.18,.18,"ESP32 / K10","I2S · UART · RGB_DATA\nmain control + UI host",PURPLE)
    block(.49,.53,.15,.12,"SOIL PROBE","TOUCH_OUT\nanalog moisture",MINT)
    block(.68,.53,.16,.12,"AUDIO + STATUS","SPK_P / SPK_N\nLED1 · LED2",CORAL)
    block(.855,.53,.09,.12,"HEADERS","J1–J11\nservice I/O",GOLD)
    # rails
    for y,lab,c in [(.40,"P5V",BLUE),(.34,"P3V3",MINT),(.28,"GND",MUTED)]:
        ax.plot([.08,.92],[y,y],color=c,lw=1,alpha=.75)
        ax.text(.055,y,lab,color=c,fontsize=7,ha="right",va="center",fontweight="bold")
    # connectors and arrows
    arrows=[((.215,.58),(.27,.58),BLUE),((.45,.58),(.49,.59),MINT),((.45,.56),(.68,.59),CORAL),((.45,.53),(.855,.59),GOLD)]
    for a,b,c in arrows:
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=11,color=c,lw=1.4))
    for x in [.14,.36,.56,.76,.9]:
        ax.add_patch(Circle((x,.4),.008,fc=BG,ec=INK,lw=.8))
    # net labels
    labels=[(.19,.62,"P5V"),( .45,.64,"UART_TX / RX"),(.53,.68,"TOUCH_OUT"),(.70,.68,"I2S_BCLK · DIN · LRCLK"),(.80,.46,"SERVO_PWM")]
    for x,y,t in labels: ax.text(x,y,t,color=INK,fontsize=6.2,ha="center")
    ax.text(.075,.17,"SIGNAL FLOW",color=GOLD,fontsize=7,fontweight="bold")
    ax.text(.075,.145,"Power enters cleanly, compute stays central, and every user-facing cue exits through sensing, audio, light, or service headers.",color=MUTED,fontsize=7.5)
    save(fig,"03_schematic_architecture_render.png")


def render_closeup():
    fig, ax = plt.subplots(figsize=(12,8), dpi=180)
    style_ax(ax, "BloomBuddy — power & feedback close-up", "Detail view of the lower-right board cluster: USB-C, charge path, LEDs, audio, and external headers")
    rounded(ax,(.04,.08),.92,.80,fc="#091b22",ec="#173d45",radius=.02)
    # zoom board
    board_shape(ax,.10,.16,.58,.62,fc="#174b4b",ec=MINT,lw=2)
    # copper traces stylized
    for i in range(14):
        x=.16+i*.036
        ax.plot([x,.42+i*.012],[.22,.70-i*.014],color=COPPER,alpha=.4,lw=1)
    for x,y,w,h,lab,col in [(.60,.66,.07,.10,"USB-C",BLUE),(.48,.62,.08,.08,"U4\nCHG",CORAL),(.34,.52,.09,.09,"U3\nPOWER",CORAL),(.55,.42,.06,.04,"D1",CORAL),(.53,.34,.06,.04,"D2",CORAL),(.20,.25,.08,.06,"J7",MINT),(.59,.25,.07,.06,"J9",MINT)]:
        rounded(ax,(x-w/2,y-h/2),w,h,fc="#132934",ec=col,radius=.008,lw=1.5)
        ax.text(x,y,lab,ha="center",va="center",color=col,fontsize=7,fontweight="bold")
    # annotations
    notes=[(.76,.67,"01  USB-C ENTRY","USB_VBUS + CC1/CC2\nserviceable power interface",BLUE),(.76,.49,"02  CHARGE / SYS","BAT_POS · BAT_NTC\nCHG_SYS · SYS_ENABLE",CORAL),(.76,.31,"03  HUMAN FEEDBACK","D1 / D2 status LEDs\nSPK_P · SPK_N audio rail",GOLD),(.76,.14,"04  EXTERNAL I/O","J7 / J9 headers\nclean handoff to enclosure",MINT)]
    for x,y,t,d,c in notes:
        ax.plot([.68,x-.02],[y+.02,y+.02],color=c,lw=1)
        ax.text(x,y+.045,t,color=c,fontsize=8,fontweight="bold")
        ax.text(x,y-.01,d,color=INK,fontsize=7,linespacing=1.35)
    ax.text(.10,.115,"THE LITTLE DETAILS MATTER",color=GOLD,fontsize=7,fontweight="bold")
    ax.text(.10,.092,"Compact routing, explicit test headers, and visible status paths keep BloomBuddy friendly to build and debug.",color=MUTED,fontsize=7.5)
    save(fig,"04_power_feedback_closeup.png")


def render_exploded():
    fig, ax = plt.subplots(figsize=(14,8), dpi=180)
    style_ax(ax, "BloomBuddy — exploded system view", "A made-for-presentation assembly view using the repository’s STEP/BOM design intent")
    rounded(ax,(.04,.08),.92,.80,fc="#091b22",ec="#173d45",radius=.02)
    # ground grid
    for x in np.linspace(.1,.9,9): ax.plot([x,x],[.18,.82],color="#12353b",lw=.5)
    for y in np.linspace(.2,.8,7): ax.plot([.08,.92],[y,y],color="#12353b",lw=.5)
    # enclosure shell
    rounded(ax,(.09,.26),.22,.38,fc="#17363b",ec="#70d8b6",radius=.035,lw=1.7)
    rounded(ax,(.12,.30),.16,.30,fc="#0c2229",ec="#3e8277",radius=.02,lw=1)
    ax.text(.20,.245,"PRINTED HOUSING",ha="center",color=INK,fontsize=8,fontweight="bold")
    # plate
    rounded(ax,(.40,.34),.18,.25,fc="#24484a",ec=MINT,radius=.015,lw=1.6)
    ax.add_patch(Circle((.49,.465),.06,fc="#10252b",ec=GOLD,lw=1.5))
    ax.text(.49,.26,"FRONT PLATE",ha="center",color=INK,fontsize=8,fontweight="bold")
    # board
    board_shape(ax,.68,.35,.19,.28,fc="#174b4b",ec=MINT,lw=2)
    rounded(ax,(.72,.45),.08,.055,fc="#132431",ec=PURPLE,radius=.008,lw=1)
    ax.text(.76,.477,"K10 / ESP32",ha="center",va="center",fontsize=6,color=PURPLE,fontweight="bold")
    ax.text(.775,.27,"REV A CONTROL BOARD",ha="center",color=INK,fontsize=8,fontweight="bold")
    # battery and sensor pieces
    rounded(ax,(.39,.72),.20,.07,fc="#23343e",ec=BLUE,radius=.012,lw=1.3)
    ax.text(.49,.755,"3.7 V / 600 mAh LiPo",ha="center",va="center",color=INK,fontsize=7)
    ax.plot([.49,.49],[.70,.60],color=BLUE,lw=1,ls="--")
    ax.add_patch(Circle((.78,.73),.035,fc="#254f45",ec=MINT,lw=1.5))
    ax.plot([.78,.78],[.70,.63],color=MINT,lw=1,ls="--")
    ax.text(.78,.785,"ANALOG SOIL PROBE",ha="center",color=INK,fontsize=8,fontweight="bold")
    # arrows / assembly axis
    ax.add_patch(FancyArrowPatch((.31,.45),(.39,.45),arrowstyle="-|>",mutation_scale=13,color=GOLD,lw=1.3,ls="--"))
    ax.add_patch(FancyArrowPatch((.59,.45),(.68,.45),arrowstyle="-|>",mutation_scale=13,color=GOLD,lw=1.3,ls="--"))
    # BOM facts
    rounded(ax,(.08,.12),.84,.08,fc="#102b32",ec="#2c5c62",radius=.012)
    ax.text(.10,.165,"ASSEMBLY NOTES",color=GOLD,fontsize=7,fontweight="bold")
    ax.text(.10,.137,"5 printed parts  ·  K10 host  ·  LiPo power  ·  32 GB microSD  ·  M2/M3/M4 hardware  ·  probe + 3-pin cable",color=MUTED,fontsize=7)
    save(fig,"05_exploded_system_view.png")


if __name__ == "__main__":
    render_hero()
    render_pcb()
    render_schematic()
    render_closeup()
    render_exploded()
    print("Generated:")
    for p in sorted(OUT.glob("*.png")):
        print(p)

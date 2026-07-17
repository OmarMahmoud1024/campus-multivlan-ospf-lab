"""
Redraws the campus topology diagram from scratch.

The only artifact that survived from the original project was a screenshot
of the finished Packet Tracer canvas (no .pkt file). This script rebuilds
that diagram as a vector figure so the repo has a clean, versioned topology
image instead of a re-uploaded phone/screenshot photo.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
import matplotlib.lines as mlines

fig, ax = plt.subplots(figsize=(19, 8))
ax.set_xlim(0, 190)
ax.set_ylim(0, 80)
ax.axis("off")

VLAN_COLORS = {
    10: "#fff44f",
    20: "#1b8a6b",
    30: "#e9a3e0",
    40: "#f5b979",
    50: "#a6e8f0",
    100: "#8ee08e",
}

def vlan_box(x, y, w, h, vlan, subnet, color, text_color="black"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="black", linewidth=1, zorder=1))
    ax.text(x + w - 2, y + h - 4, f"VLAN {vlan}\n{subnet}", fontsize=9, ha="right", va="top",
             color=text_color, fontweight="bold", zorder=3,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5))

def device(x, y, label, kind="pc"):
    if kind == "pc":
        ax.add_patch(Rectangle((x - 1.6, y - 1.1), 3.2, 2.2, facecolor="#dfe6ee", edgecolor="black", zorder=4))
        ax.text(x, y - 2.2, label, fontsize=7.5, ha="center", va="top", zorder=4)
    elif kind == "switch":
        ax.add_patch(mpatches.RegularPolygon((x, y), numVertices=4, radius=2.2, orientation=0.785,
                                              facecolor="#c9c9c9", edgecolor="black", zorder=4))
        ax.text(x, y - 3.2, label, fontsize=8, ha="center", va="top", fontweight="bold", zorder=4)
    elif kind == "router":
        ax.add_patch(plt.Circle((x, y), 2.3, facecolor="#f2b6b6", edgecolor="black", zorder=4))
        ax.text(x, y - 3.6, label, fontsize=8.5, ha="center", va="top", fontweight="bold", zorder=4)
    elif kind == "server":
        ax.add_patch(Rectangle((x - 1.4, y - 2), 2.8, 4, facecolor="#cfd8dc", edgecolor="black", zorder=4))
        ax.text(x, y - 3.2, label, fontsize=7.5, ha="center", va="top", zorder=4)

def link(p1, p2, color="black", style="-", lw=1.6, label=None, label_color="black"):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=style, linewidth=lw, zorder=2)
    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + 1.5, label, fontsize=8, ha="center", color=label_color, fontweight="bold", zorder=5,
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))

# VLAN zone boxes
vlan_box(2, 60, 40, 18, 10, "192.168.10.0/24", VLAN_COLORS[10])
vlan_box(2, 40, 22, 18, 20, "192.168.20.0/24", VLAN_COLORS[20])
vlan_box(25, 30, 22, 18, 30, "192.168.30.0/24", VLAN_COLORS[30])
vlan_box(2, 5, 24, 22, 40, "192.168.40.0/24", VLAN_COLORS[40])
vlan_box(148, 55, 40, 20, 50, "192.168.50.0/24", VLAN_COLORS[50])
ax.add_patch(Rectangle((148, 30), 40, 20, facecolor=VLAN_COLORS[100], edgecolor="black", linewidth=1, zorder=1))

# PCs
device(12, 72, "PC4", "pc"); device(24, 74, "PC5", "pc"); device(10, 52, "PC6", "pc")
device(35, 42, "PC0", "pc"); device(43, 40, "PC1", "pc")
device(10, 20, "PC3", "pc"); device(18, 16, "PC2", "pc")
device(160, 68, "PC8", "pc"); device(172, 70, "PC9", "pc")
ax.text(165, 45, "VLAN 100\n192.168.100.0/24", fontsize=9, ha="center", fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5))
device(165, 38, "Server0", "server")

device(95, 70, "PC10", "pc")
device(180, 20, "PC11", "pc")

# Switches
device(28, 62, "S1", "switch")
device(36, 22, "S3", "switch")
device(150, 62, "S2", "switch")
device(85, 22, "S4", "switch")
device(160, 20, "S5", "switch")

# Routers
device(60, 62, "R1", "router")
device(85, 45, "R2", "router")
device(60, 30, "R3", "router")
device(110, 25, "R4", "router")
device(150, 20, "R5", "router")

# Access links
link((12, 72), (26, 63)); link((24, 74), (28, 64)); link((10, 52), (27, 61))
link((35, 42), (36, 24)); link((43, 40), (37, 23))
link((10, 20), (35, 22)); link((18, 16), (35, 21))
link((160, 68), (151, 63)); link((172, 70), (151, 62))
link((165, 38), (151, 61.5))
link((95, 70), (85.5, 22.5))
link((180, 20), (161, 20))

# Switch <-> router
link((30, 62), (58, 62.5))
link((37, 22), (58, 29))

# Router <-> router (OSPF backbone in red, static R4-R5 dashed)
link((62, 61), (84, 46.5), color="red", lw=2.2, label="10.10.10.0/24")
link((84, 44), (62, 31), color="red", lw=2.2, label="10.10.20.0/24")
link((86, 43), (111, 26.5), color="black", style=(0, (5, 3)), lw=2, label="10.10.50.0/24", label_color="#555555")
link((86, 46), (149, 61), color="black", lw=1.8)

# S4 / R4, S5 / R5, R4-R5
link((87, 24), (105, 25), label="172.16.0.0/16")
link((113, 24), (149, 21), color="black", style=(0, (5, 3)), lw=2, label="20.20.20.0/24")
link((152, 20), (159, 20), label="192.168.200.0/24")

# Legend
red_line = mlines.Line2D([], [], color="red", lw=2.2, label="OSPF area 0 link")
dash_line = mlines.Line2D([], [], color="black", lw=2, linestyle=(0, (5, 3)), label="Static route link (R4–R5)")
plain_line = mlines.Line2D([], [], color="black", lw=1.6, label="Access / trunk link")
ax.legend(handles=[red_line, dash_line, plain_line], loc="lower center", ncol=3,
          bbox_to_anchor=(0.5, -0.06), frameon=False, fontsize=9)

ax.text(95, 78, "Campus Multi-VLAN / OSPF Lab — Topology", fontsize=15, ha="center", fontweight="bold")

plt.tight_layout()
plt.savefig("/sessions/awesome-serene-cannon/mnt/outputs/campus-multivlan-ospf-lab/topology.png", dpi=200, bbox_inches="tight")
print("saved")

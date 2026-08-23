"""
KGR (%) / BMR (%) vs Quantization Levels (q) — versi publication-ready.

Encoding:
  Skenario -> WARNA (Okabe-Ito, colorblind-safe) + BENTUK MARKER (redundansi)
  Metrik   -> GARIS: KGR = dashed + marker hollow, BMR = solid + marker filled
  Sumbu-x  -> skala log basis 2 (q menggandakan)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator, FixedLocator, FixedFormatter

# ----------------------------------------------------------------------
# DATA
# ----------------------------------------------------------------------
q = np.array([2, 4, 8, 16, 32, 64])

kgr = {
    "Scenario 1": [10, 11, 15, 19, 24, 29],
    "Scenario 2": [3,  3,  4,  8,  12, 17],
    "Scenario 3": [7,  9,  11, 13, 18, 23],
}
bmr = {
    "Scenario 1": [10, 9,  8,  7,  6,  5],
    "Scenario 2": [53, 10, 9,  8,  7,  6],
    "Scenario 3": [9,  18, 27, 36, 45, 54],
}

# Okabe-Ito colorblind-safe palette
colors = {
    "Scenario 1": "#0072B2",   # biru
    "Scenario 2": "#E69F00",   # oranye
    "Scenario 3": "#009E73",   # hijau-kebiruan
}
# marker berbeda per skenario (redundansi selain warna)
markers = {
    "Scenario 1": "o",         # lingkaran
    "Scenario 2": "s",         # kotak
    "Scenario 3": "^",         # segitiga
}

selected_q = 8

# ----------------------------------------------------------------------
# STYLING
# ----------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "axes.linewidth": 1.4,
    "lines.antialiased": True,
})

fig, ax = plt.subplots(figsize=(10, 5.8))

LW = 2.4
MS = 8
MEW = 1.8

# --- KGR: dashed + marker hollow ---
for name, y in kgr.items():
    ax.plot(q, y,
            linestyle="--", linewidth=LW,
            marker=markers[name], markersize=MS,
            markerfacecolor="white",
            markeredgecolor=colors[name], markeredgewidth=MEW,
            color=colors[name],
            solid_capstyle="round", dash_capstyle="round", zorder=3)

# --- BMR: solid + marker filled ---
for name, y in bmr.items():
    ax.plot(q, y,
            linestyle="-", linewidth=LW,
            marker=markers[name], markersize=MS,
            markerfacecolor=colors[name],
            markeredgecolor="white", markeredgewidth=1.1,
            color=colors[name],
            solid_capstyle="round", zorder=4)

# --- garis vertikal q terpilih + shading tipis ---
ax.axvline(selected_q, color="0.45", linestyle="--", linewidth=1.5, zorder=1)
ax.axvspan(selected_q / 1.18, selected_q * 1.18, color="0.5", alpha=0.06, zorder=0)
ax.annotate(f"Selected q = {selected_q}",
            xy=(selected_q, 57), ha="center", va="center",
            fontsize=12, zorder=6,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.6", lw=1.2))

# ----------------------------------------------------------------------
# SUMBU log-2 + GRID
# ----------------------------------------------------------------------
ax.set_xscale("log", base=2)
ax.xaxis.set_major_locator(FixedLocator(q))
ax.xaxis.set_major_formatter(FixedFormatter([str(v) for v in q]))
ax.xaxis.set_minor_locator(FixedLocator([]))      # buang minor tick log
ax.set_xlim(q[0] / 1.15, q[-1] * 1.15)

ax.set_ylim(0, 60)
ax.yaxis.set_major_locator(MultipleLocator(10))

ax.set_xlabel("Quantization Levels (q)", fontsize=15, fontweight="bold")
ax.set_ylabel("KGR (%) / BMR (%)", fontsize=15, fontweight="bold")

ax.grid(True, which="major", linestyle=":", linewidth=0.8, color="0.8", zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# ----------------------------------------------------------------------
# LEGEND — dua blok terpisah biar ringkas & jelas:
#   (a) skenario  -> warna + bentuk
#   (b) metrik    -> gaya garis (KGR dashed hollow / BMR solid filled)
# ----------------------------------------------------------------------
scenario_handles = [
    Line2D([0], [0], color=colors[n], marker=markers[n], linestyle="none",
           markersize=MS, markerfacecolor=colors[n], markeredgecolor="white",
           markeredgewidth=1.1, label=n)
    for n in colors
]
metric_handles = [
    Line2D([0], [0], color="0.25", linestyle="--", linewidth=LW,
           marker="o", markersize=MS, markerfacecolor="white",
           markeredgecolor="0.25", markeredgewidth=MEW, label="KGR (dashed)"),
    Line2D([0], [0], color="0.25", linestyle="-", linewidth=LW,
           marker="o", markersize=MS, markerfacecolor="0.25",
           markeredgecolor="white", markeredgewidth=1.1, label="BMR (solid)"),
]

leg1 = ax.legend(handles=scenario_handles, loc="upper left",
                 frameon=False, fontsize=11, title="Scenario",
                 title_fontsize=11, labelspacing=0.5,
                 bbox_to_anchor=(1.015, 1.0))
leg1.get_title().set_fontweight("bold")
ax.add_artist(leg1)

ax.legend(handles=metric_handles, loc="upper left",
          frameon=False, fontsize=11, title="Metric",
          title_fontsize=11, labelspacing=0.5, handlelength=2.6,
          bbox_to_anchor=(1.015, 0.62)).get_title().set_fontweight("bold")

fig.tight_layout()
fig.savefig("kgr_bmr_quantization_v2.png", dpi=300, bbox_inches="tight")
fig.savefig("kgr_bmr_quantization_v2.pdf", bbox_inches="tight")   # vektor untuk LaTeX
print("saved v2 png + pdf")
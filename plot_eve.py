"""
Figure 11 - Bit Disagreement Rate (BDR) comparison:
Legitimate link (Alice-Bob) vs Eavesdropper link (Alice-Eve)
across the three outdoor scenarios.

Output: PNG at 300 dpi (IJIES-compliant: >=10 pt fonts, no outer border,
no in-figure (a)(b) labels, original figure).

Run:  python plot_bdr_eve.py
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# ---- global style (unified font, >=10 pt) ----
mpl.rcParams.update({
    "font.family": "serif",          # Times-like to match the paper
    "font.size": 11,
    "axes.titlesize": 11,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

scenarios = ["Scenario 1", "Scenario 2", "Scenario 3"]

# Data from the auto-evaluation pipeline
initial_bob = [13.04, 4.50, 7.64]     # Alice-Bob initial BDR (%)
final_bob   = [0.00, 0.00, 0.00]      # Alice-Bob final-key BDR (%)
initial_eve = [44.06, 63.09, 56.77]   # Alice-Eve initial BDR (%)
final_eve   = [50.96, 49.96, 50.03]   # Alice-Eve final-key BDR (%)

x = np.arange(len(scenarios))
w = 0.20  # bar width

fig, ax = plt.subplots(figsize=(7.0, 3.6))  # wide -> one-column span in the paper

b1 = ax.bar(x - 1.5*w, initial_bob, w, label="Alice–Bob (initial)",
            color="#2E5A88", edgecolor="black", linewidth=0.5)
b2 = ax.bar(x - 0.5*w, final_bob,   w, label="Alice–Bob (final BDR)",
            color="#8FB0D0", edgecolor="black", linewidth=0.5)
b3 = ax.bar(x + 0.5*w, initial_eve, w, label="Alice–Eve (initial)",
            color="#A83232", edgecolor="black", linewidth=0.5)
b4 = ax.bar(x + 1.5*w, final_eve,   w, label="Alice–Eve (final BDR)",
            color="#E0A0A0", edgecolor="black", linewidth=0.5, hatch="//")

# 50% random-guessing reference line
ax.axhline(50, color="gray", linestyle="--", linewidth=1.0)
ax.text(-0.42, 63.5, "– – 50%: random-guessing level",
        ha="left", va="bottom", fontsize=9, color="gray")

# value labels on top of each bar
for bars in (b1, b2, b3, b4):
    for r in bars:
        h = r.get_height()
        ax.annotate(f"{h:.2f}", (r.get_x()+r.get_width()/2, h),
                    ha="center", va="bottom", fontsize=8,
                    xytext=(0, 1), textcoords="offset points")

ax.set_ylabel("Bit Disagreement Rate (%)")
ax.set_xticks(x)
ax.set_xticklabels(scenarios)
ax.set_ylim(0, 68)
ax.legend(ncol=4, loc="upper center", frameon=False,
          bbox_to_anchor=(0.5, -0.12), columnspacing=1.0, handletextpad=0.5)

# remove top/right spines (no outer border box)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="both", length=3)

plt.tight_layout()
plt.savefig("Fig11_BDR_Eve.png", dpi=300, bbox_inches="tight")
# also a vector copy if you want to embed as PDF/EPS:
plt.savefig("Fig11_BDR_Eve.pdf", bbox_inches="tight")
print("Saved: Fig11_BDR_Eve.png (300 dpi) and Fig11_BDR_Eve.pdf")
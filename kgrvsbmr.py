import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from pathlib import Path

# Data reconstructed from the reference chart
q = np.array([2, 4, 8, 16, 32, 64])

# KGR (dashed, open marker)
kgr_s1 = np.array([10, 11, 15, 19, 24, 29])
kgr_s2 = np.array([3, 3, 4, 7, 11, 17])
kgr_s3 = np.array([7, 9, 11, 13, 18, 23])

# BMR (solid, filled marker)
bmr_s1 = np.array([10, 9, 8, 7, 5.5, 4.5])
bmr_s2 = np.array([53, 9.5, 8, 7, 6, 5])
bmr_s3 = np.array([9, 18, 27, 36, 45, 54])

fig, ax = plt.subplots(figsize=(9.2, 6.1))

# Plot KGR (dashed, open markers)
line1, = ax.plot(q, kgr_s1, '--', marker='o', mfc='white', linewidth=1.8, markersize=6)
line2, = ax.plot(q, kgr_s2, '--', marker='s', mfc='white', linewidth=1.8, markersize=6)
line3, = ax.plot(q, kgr_s3, '--', marker='^', mfc='white', linewidth=1.8, markersize=6)

# Plot BMR (solid, filled markers)
ax.plot(q, bmr_s1, '-', marker='o', linewidth=1.8, markersize=5)
ax.plot(q, bmr_s2, '-', marker='s', linewidth=1.8, markersize=5)
ax.plot(q, bmr_s3, '-', marker='^', linewidth=1.8, markersize=5)

# Highlight selected q = 8
ax.axvspan(7.2, 8.8, alpha=0.08)
ax.axvline(8, linestyle='--', linewidth=1.2, color='0.35')
ax.annotate(
    'Selected q = 8',
    xy=(8, 56.5),
    ha='center',
    va='center',
    fontsize=10,
    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='0.4')
)

# Axes formatting
ax.set_xlim(1.8, 66)
ax.set_ylim(0, 60)
ax.set_xscale('log', base=2)
ax.set_xticks(q)
ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())

ax.set_xlabel('Quantization Levels (q)', fontsize=12, fontweight='bold')
ax.set_ylabel('KGR (%) / BMR (%)', fontsize=12, fontweight='bold')

ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.35)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Legend handles
scenario_handles = [
    Line2D([0], [0], marker='o', linestyle='None', markersize=7, label='Scenario 1'),
    Line2D([0], [0], marker='s', linestyle='None', markersize=7, label='Scenario 2'),
    Line2D([0], [0], marker='^', linestyle='None', markersize=7, label='Scenario 3'),
]

metric_handles = [
    Line2D([0], [0], linestyle='--', marker='o', markerfacecolor='white',
           markeredgecolor='black', color='black', linewidth=1.5,
           markersize=6, label='KGR (dashed)'),
    Line2D([0], [0], linestyle='-', marker='o', markerfacecolor='black',
           markeredgecolor='black', color='black', linewidth=1.5,
           markersize=5, label='BMR (solid)'),
]

# Two horizontal legends placed side-by-side below the plot
leg1 = fig.legend(
    handles=scenario_handles,
    title='Scenario',
    loc='lower center',
    bbox_to_anchor=(0.33, 0.025),
    frameon=False,
    ncol=3,
    fontsize=10,
    title_fontsize=10,
    columnspacing=1.5,
    handletextpad=0.6
)

leg2 = fig.legend(
    handles=metric_handles,
    title='Metric',
    loc='lower center',
    bbox_to_anchor=(0.77, 0.025),
    frameon=False,
    ncol=2,
    fontsize=10,
    title_fontsize=10,
    columnspacing=1.5,
    handletextpad=0.8
)

leg1.get_title().set_fontweight('bold')
leg2.get_title().set_fontweight('bold')

# Extra bottom space for the side-by-side legends
plt.subplots_adjust(bottom=0.27)

# Save at 300 DPI
output_dir = Path(__file__).resolve().parent / 'output_images'
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'quantization_tradeoff_legend_below_sidebyside_300dpi.png'

plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f'Gambar tersimpan di: {output_path}')

plt.show()

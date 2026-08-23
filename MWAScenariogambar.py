import os
import matplotlib.pyplot as plt
import numpy as np

# ===========================
# Data
# ===========================
window = [5, 10, 15, 20, 25, 30, 40, 50]

scenario1 = [0.695, 0.820, 0.880, 0.920, 0.940, 0.950, 0.965, 0.972]
scenario2 = [0.950, 0.980, 0.988, 0.990, 0.991, 0.992, 0.993, 0.994]
scenario3 = [0.855, 0.920, 0.950, 0.965, 0.973, 0.978, 0.985, 0.987]

# ===========================
# Figure
# ===========================
plt.figure(figsize=(8,4.5), dpi=300)

# Plot tiap skenario
plt.plot(window, scenario1,
         color='blue',
         marker='o',
         linewidth=2,
         markersize=5,
         label='Scenario 1')

plt.plot(window, scenario2,
         color='green',
         marker='o',
         linewidth=2,
         markersize=5,
         label='Scenario 2')

plt.plot(window, scenario3,
         color='red',
         marker='^',
         linewidth=2,
         markersize=5,
         label='Scenario 3')

# ===========================
# Highlight Window Size = 25
# ===========================

selected = 25
idx = window.index(selected)

# Garis vertikal
plt.axvline(x=selected,
            color='black',
            linestyle='--',
            linewidth=1.5,
            zorder=0)

# Highlight titik pada ketiga kurva
plt.scatter(selected, scenario1[idx],
            s=200,
            color='gold',
            edgecolor='black',
            linewidth=2,
            zorder=10)

plt.scatter(selected, scenario2[idx],
            s=200,
            color='gold',
            edgecolor='black',
            linewidth=2,
            zorder=10)

plt.scatter(selected, scenario3[idx],
            s=200,
            color='gold',
            edgecolor='black',
            linewidth=2,
            zorder=10)

# Anotasi
plt.annotate(
    'Selected Window Size (N = 25)',
    xy=(25, scenario1[idx] - 0.008),
    xytext=(28, 0.80),
    fontsize=10,
    fontweight='bold',
    arrowprops=dict(
        arrowstyle='->',
        lw=1.5,
        color='black'
    )
)

# ===========================
# Format Grafik
# ===========================

plt.xlabel('MWA Window Size (N)', fontsize=12)
plt.ylabel('Pearson Correlation ($\\rho$)', fontsize=12)

plt.xlim(4,51)
plt.ylim(0.69,1.00)

plt.xticks(window)
plt.yticks(np.arange(0.70,1.01,0.05))

plt.grid(True,
         linestyle='--',
         linewidth=0.5,
         alpha=0.5)

plt.legend(loc='lower right', fontsize=9)

plt.tight_layout()

# ===========================
# Simpan Gambar
# ===========================
output_dir = 'comparison'
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, 'Pearson_Correlation_MWA_Window.png')
plt.savefig(
    output_path,
    dpi=300,
    bbox_inches='tight'
)
print(f"Grafik berhasil disimpan di: {output_path}")

plt.show()
import os
import matplotlib.pyplot as plt
import numpy as np

# Data
labels = ['[11]', '[12]', '[13]', '[14]', '[15]', 'This Work']
values = [0.585, 0.421, 0.918, 0.421, 0.784, 0.937]

# Figure
plt.figure(figsize=(7.5, 5))

# Bars
bars = plt.bar(labels, values)

# Title and labels
plt.title('Pearson correlation after preprocessing comparison', fontweight='normal', fontsize=12)
plt.ylabel('Pearson Correlation Coefficient', fontweight='normal', fontsize=12)

# Y-axis limits
plt.ylim(0, 1.05)

# Value labels on top of bars
for bar, value in zip(bars, values):
    plt.text(
        bar.get_x() + bar.get_width()/2,
        value + 0.015,
        f'{value:.3f}',
        ha='center',
        va='bottom',
        fontsize=10
    )

# Mengatur grid agar mirip dengan contoh foto (warna abu-abu tipis, di semua sumbu)
plt.grid(True, which='major', axis='both', color='#e6e6e6', linestyle='-', linewidth=0.8)
plt.gca().set_axisbelow(True)

plt.tight_layout()

# Membuat folder 'comparison' jika belum ada
output_dir = 'comparison'
os.makedirs(output_dir, exist_ok=True)

# Menyimpan gambar dengan resolusi 300 DPI
output_path = os.path.join(output_dir, 'Pearson_Correlation_Comparison.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Grafik berhasil disimpan di: {output_path}")

plt.show()
import os
import matplotlib.pyplot as plt

labels = ['[11]', '[12]', '[13]', '[14]', '[15]', 'HySKG']
values = [6.93, 1.97, 1.24, 1.99, 1.99, 25.99]

plt.figure(figsize=(8, 5))

bars = plt.bar(labels, values, width=0.55, color=['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a'])

plt.title('Total KGR (End-to-End) Comparison', fontweight='bold', fontsize=12)
plt.ylabel('Total KGR (bps)', fontweight='bold', fontsize=12)
plt.ylim(0, max(values) * 1.1)

# Offset text labels dynamically by 1.5% of max value
offset = max(values) * 0.015

for bar, value in zip(bars, values):
    plt.text(
        bar.get_x() + bar.get_width()/2,
        value + offset,
        f'{value}',
        ha='center',
        va='bottom',
        fontsize=9,
        fontweight='normal'
    )

# Menambahkan grid yang bersih
plt.grid(True, which='major', axis='both', color='#e6e6e6', linestyle='-', linewidth=0.8)
plt.gca().set_axisbelow(True)

# Pastikan bingkai (border) hitam mengelilingi grafik penuh
for spine in plt.gca().spines.values():
    spine.set_visible(True)
    spine.set_color('black')
    spine.set_linewidth(1.0)

plt.tight_layout()

# Membuat folder 'comparison' jika belum ada
output_dir = 'comparison'
os.makedirs(output_dir, exist_ok=True)

# Menyimpan gambar dengan resolusi 300 DPI
output_path = os.path.join(output_dir, 'Total_KGR_Comparison.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Grafik berhasil disimpan di: {output_path}")

plt.show()
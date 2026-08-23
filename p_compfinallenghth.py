import os
import matplotlib.pyplot as plt

labels = ['[11]', '[12]', '[13]', '[14]', '[15]', 'This Work']
values = [888, 256, 160, 256, 256, 3328]

plt.figure(figsize=(7.5, 5))

bars = plt.bar(labels, values, width=0.55)

plt.title('Final Length Comparison', fontweight='bold', fontsize=15)
plt.ylabel('Final Length (bit)', fontweight='bold', fontsize=18)
plt.ylim(0, 4500)

for bar, value in zip(bars, values):
    plt.text(
        bar.get_x() + bar.get_width()/2,
        value + 70,
        f'{value}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

# Menambahkan grid yang bersih seperti pada referensi foto
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
output_path = os.path.join(output_dir, 'Final_Key_Length_Comparison.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Grafik berhasil disimpan di: {output_path}")

plt.show()
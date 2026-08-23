import matplotlib.pyplot as plt
import numpy as np

def main():
    # Data dari hasil uji NIST Approximate Entropy
    scenarios = ['[11]', '[12]', '[13]', '[14]', '[15]', 'This Work']
    
    # Nilai entropy Alice dan Bob
    entropy_alice = [0.978193, 0.996296, 0.957094, 0.990156, 0.949798, 0.993303]
    entropy_bob = [0.978193, 0.996296, 0.957094, 0.990156, 0.949798, 0.993303]
    
    x = np.arange(len(scenarios))  # Posisi label pada sumbu X
    width = 0.35  # Lebar batang
    
    # Membuat figure dengan ukuran yang ideal untuk paper/tesis
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    # Menggunakan palet warna modern dan kontras
    # Alice: Deep Blue, Bob: Warm Amber
    color_alice = '#1f77b4'  # Steel Blue
    color_bob = '#ff7f0e'   # Safety Orange (atau bisa diganti #2ca02c Hijau)
    
    # Membuat diagram batang berkelompok
    rects1 = ax.bar(x - width/2, entropy_alice, width, label='Alice', color=color_alice, edgecolor='black', linewidth=0.8, alpha=0.9)
    rects2 = ax.bar(x + width/2, entropy_bob, width, label='Bob', color=color_bob, edgecolor='black', linewidth=0.8, alpha=0.9, hatch='//')
    
    # Menambahkan label teks, judul, dan penamaan sumbu
    ax.set_ylabel('Approximate Entropy Value', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('NIST Approximate Entropy Comparison\nAlice vs Bob across Scenarios', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=11, fontweight='bold')
    
    # Batas sumbu Y dilebihkan sedikit agar label teks di atas batang tidak terpotong
    ax.set_ylim(0, 1.15)
    
    # Menambahkan legenda (Legend) dengan tampilan modern
    ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='gray', shadow=True, fontsize=11)
    
    # Menambahkan gridline horizontal yang halus
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    # Memastikan batang digambar di atas gridline
    ax.set_axisbelow(True)
    
    # Fungsi untuk menyematkan nilai di atas masing-masing batang
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.6f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5),  # Offset 5 poin ke atas
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
            
    autolabel(rects1)
    autolabel(rects2)
    
    # Layout otomatis agar rapi
    plt.tight_layout()
    
    # Menyimpan grafik dengan resolusi tinggi (300 DPI) untuk kualitas cetak tesis
    output_filename = 'Grafik_Entropy_NIST.png'
    plt.savefig(output_filename, dpi=300)
    print(f"Grafik berhasil dibuat dan disimpan sebagai: {output_filename}")
    
    # Menampilkan plot
    plt.show()

if __name__ == '__main__':
    main()

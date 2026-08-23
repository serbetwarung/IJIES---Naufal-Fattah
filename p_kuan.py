import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # Tambahan untuk plotting

# Parameter
BLOCK_SIZE_QUANT = 64
INTERVAL_SAMPLING_DETIK = 0.110  # Delay channel probing 110 ms (ping interval)

def local_block_quantization(data):
    bits = []
    for i in range(0, len(data), BLOCK_SIZE_QUANT):
        block = data[i:i + BLOCK_SIZE_QUANT]
        if len(block) == 0: continue
        
        median_val = np.median(block)
        # Sinyal diubah menjadi bit biner
        block_bits = (block >= median_val).astype(int)
        bits.extend(block_bits)
        
    return np.array(bits)

def plot_quantization_scatter(data, output_filename, block_size=64):
    """Menggambar visualisasi proses kuantisasi pada 1 blok pertama"""
    print("Menggambar grafik visualisasi kuantisasi (menyimpan ke PNG)...")
    
    # Kita ambil 1 blok pertama saja agar grafiknya jelas dan tidak berdesakan
    subset = data[:block_size]
    if len(subset) == 0:
        return
        
    waktu = np.arange(len(subset))
    median_val = np.median(subset)
    
    # Pisahkan indeks untuk bit 1 dan bit 0 agar warnanya beda
    bit_1_idx = np.where(subset >= median_val)[0]
    bit_0_idx = np.where(subset < median_val)[0]
    
    plt.figure(figsize=(10, 5))
    
    # Plot garis sinyal tipis sebagai penghubung
    plt.plot(waktu, subset, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    # Scatter plot titik sinyal (Hijau untuk 1, Merah untuk 0)
    plt.scatter(bit_1_idx, subset[bit_1_idx], color='green', label='Bit 1 ($\geq$ Median)', zorder=5, s=40)
    plt.scatter(bit_0_idx, subset[bit_0_idx], color='red', label='Bit 0 (< Median)', zorder=5, s=40)
    
    # Gambar garis pembatas (Threshold) Median Lokal
    plt.axhline(y=median_val, color='blue', linestyle='--', linewidth=2, label=f'Garis Median Lokal ({median_val:.2f} dBm)')
    
    plt.title(f'Visualisasi Kuantisasi Blok Lokal (1 Blok = {block_size} Sampel)', fontsize=14, fontweight='bold')
    plt.xlabel('Indeks Sampel', fontsize=12)
    plt.ylabel('Nilai Sinyal Halus (dBm)', fontsize=12)
    plt.legend(loc='best', shadow=True)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300) # Simpan resolusi tinggi
    plt.close() # Sangat penting agar terminal tidak freeze
    print(f" -> Grafik berhasil disimpan sebagai: {output_filename}")

def main():
    print("=== TAHAP 2: Kuantisasi Blok Lokal (Dengan Kalkulasi KGR) ===")
    input_file = input("Masukkan nama file hasil pra-proses (contoh: Praproses_Skenario 1.csv): ").strip()
    
    # Menghapus tanda kutip jika file di-drag & drop
    input_file = input_file.strip('"').strip("'")
    
    if not os.path.exists(input_file):
        print("File tidak ditemukan.")
        return

    df = pd.read_csv(input_file)
    smooth_alice = df['smooth_alice'].values
    smooth_bob = df['smooth_bob'].values
    
    print("Mengekstrak bit...")
    bit_alice = local_block_quantization(smooth_alice)
    bit_bob = local_block_quantization(smooth_bob)
    
    # ==========================================
    # PERHITUNGAN KGR (Sesuai Permintaan Dosen)
    # ==========================================
    total_sampel = len(smooth_alice)
    total_waktu_detik = total_sampel * INTERVAL_SAMPLING_DETIK
    
    # 1. KGR Sebelum Kuantisasi (Initial Bit Rate / IBR)
    kgr_sebelum = total_sampel / total_waktu_detik
    
    # 2. KGR Sesudah Kuantisasi (Raw Key Generation Rate / R-KGR)
    kgr_sesudah = len(bit_alice) / total_waktu_detik
    
    # Perhitungan Error Awal
    initial_errors = int(np.sum(bit_alice != bit_bob))
    bdr = (initial_errors / len(bit_alice)) * 100
    
    # Nama Output
    base_name = os.path.splitext(os.path.basename(input_file))[0].replace("Praproses_", "")
    output_csv = f"Kuantisasi_{base_name}.csv"
    output_grafik = f"Grafik_2_Kuantisasi_{base_name}.png"
    
    # Simpan Output CSV
    pd.DataFrame({
        "bit_alice": bit_alice,
        "bit_bob": bit_bob
    }).to_csv(output_csv, index=False)
    
    # === PANGGIL FUNGSI PLOTTING DI SINI ===
    # Menggambar grafik kuantisasi menggunakan data Alice
    plot_quantization_scatter(smooth_alice, output_grafik, BLOCK_SIZE_QUANT)
    
    # Tampilkan ke Terminal untuk Laporan
    print("\n--- RINGKASAN PERFORMA KGR & ERROR ---")
    print(f"Total Sampel Sinyal        : {total_sampel} sampel")
    print(f"Total Waktu Perekaman      : {total_waktu_detik:.1f} detik")
    print(f"KGR Sebelum Kuantisasi     : {kgr_sebelum:.3f} bps (Initial Bit Rate)")
    print(f"KGR Sesudah Kuantisasi     : {kgr_sesudah:.3f} bps (Raw Key Generation Rate)")
    print(f"Efisiensi Retensi Bit      : {(kgr_sesudah/kgr_sebelum)*100:.1f}%")
    print(f"BDR Awal (Pra-rekonsiliasi): {bdr:.2f}% ({initial_errors} bit berbeda dari {len(bit_alice)} bit)")
    print(f"\nSelesai! Bit mentah disimpan di: {output_csv}\n")

if __name__ == "__main__":
    main()
import os
import pandas as pd
import numpy as np
import pywt
from scipy import stats
import matplotlib.pyplot as plt  # Tambahan untuk plotting

# Parameter
BLOCK_SIZE_PREPROCESS = 64
VAR_THRESHOLD = 5.0
COL_SIGNAL = 'wlan_radio.signal_dbm'  # Kolom RSSI pada dataset CSV

def moving_average(data, window_size=5):
    """Jalur Hemat Energi (Light Path)"""
    return np.convolve(data, np.ones(window_size)/window_size, mode='same')

def apply_dwt_sym4(data):
    """Jalur Intensif (Heavy Path)"""
    coeffs = pywt.wavedec(data, 'sym4', level=2)
    coeffs[1] = np.zeros_like(coeffs[1])
    coeffs[2] = np.zeros_like(coeffs[2])
    reconstructed = pywt.waverec(coeffs, 'sym4')
    return reconstructed[:len(data)]

def adaptive_preprocess(data):
    """Filter Adaptif berdasarkan Varians"""
    data_array = np.array(data, dtype=float)
    result = np.zeros_like(data_array)
    
    for i in range(0, len(data_array), BLOCK_SIZE_PREPROCESS):
        block = data_array[i:i + BLOCK_SIZE_PREPROCESS]
        if len(block) == 0: continue
        
        if np.var(block) < VAR_THRESHOLD:
            result[i:i + len(block)] = moving_average(block)
        else:
            result[i:i + len(block)] = apply_dwt_sym4(block)
            
    return result

def pearson_correlation(data_a, data_b):
    """Menghitung Korelasi Pearson antara dua sinyal."""
    if len(data_a) != len(data_b) or len(data_a) < 2:
        return 0.0, 1.0
    r, p_value = stats.pearsonr(data_a, data_b)
    return float(r), float(p_value)

def plot_signal_comparison(raw_data, smooth_data, output_filename, limit=150):
    """Fungsi khusus untuk menggambar dan menyimpan grafik ke file PNG"""
    print(f"Menggambar grafik perbandingan sinyal (menyimpan ke PNG)...")
    
    # Membatasi jumlah sampel yang digambar agar grafik tidak terlalu padat (misal 150 sampel pertama)
    raw_subset = raw_data[:limit]
    smooth_subset = smooth_data[:limit]
    waktu = np.arange(len(raw_subset))
    
    plt.figure(figsize=(10, 5))
    
    # Plot Sinyal Mentah (Warna pudar sebagai latar)
    plt.plot(waktu, raw_subset, label='Sinyal RSSI Mentah (Raw)', color='lightcoral', linestyle='-', marker='o', markersize=3, alpha=0.7)
    
    # Plot Sinyal Halus (Warna biru tebal)
    plt.plot(waktu, smooth_subset, label='Sinyal Halus (ADW)', color='blue', linewidth=2, marker='s', markersize=4)
    
    plt.title(f'Perbandingan Sinyal RSSI Mentah vs Pra-proses ADW ({len(raw_subset)} Sampel Pertama)', fontsize=14, fontweight='bold')
    plt.xlabel('Waktu (Detik / Sampel)', fontsize=12)
    plt.ylabel('Nilai RSSI (dBm)', fontsize=12)
    plt.legend(loc='lower right', shadow=True)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300) # Simpan resolusi tinggi untuk naskah Tesis
    plt.close() # SANGAT PENTING: Tutup plot memori agar terminal tidak freeze!
    print(f" -> Grafik berhasil disimpan sebagai: {output_filename}")

def main():
    print("=== TAHAP 1: Pra-proses Adaptif (ADW) ===")
    # Meminta input dua file CSV terpisah (Alice dan Bob)
    file_alice = input("Masukkan nama file CSV Alice (contoh: skenario1alice.csv): ").strip().strip('"').strip("'")
    file_bob   = input("Masukkan nama file CSV Bob   (contoh: skenario1bob.csv):   ").strip().strip('"').strip("'")
    
    for f in [file_alice, file_bob]:
        if not os.path.exists(f):
            print(f"File '{f}' tidak ditemukan. Pastikan nama dan lokasinya benar.")
            return

    print(f"Membaca file {file_alice} dan {file_bob}...")
    df_alice = pd.read_csv(file_alice)
    df_bob   = pd.read_csv(file_bob)

    if COL_SIGNAL not in df_alice.columns:
        print(f"Error: Kolom '{COL_SIGNAL}' tidak ditemukan di {file_alice}.")
        return
    if COL_SIGNAL not in df_bob.columns:
        print(f"Error: Kolom '{COL_SIGNAL}' tidak ditemukan di {file_bob}.")
        return

    raw_alice = df_alice[COL_SIGNAL].dropna().values
    raw_bob   = df_bob[COL_SIGNAL].dropna().values

    min_len = min(len(raw_alice), len(raw_bob))

    print("Memproses sinyal...")
    smooth_alice = adaptive_preprocess(raw_alice[:min_len])
    smooth_bob   = adaptive_preprocess(raw_bob[:min_len])

    # ==========================================
    # KORELASI PEARSON
    # ==========================================
    r_raw,    p_raw    = pearson_correlation(raw_alice[:min_len], raw_bob[:min_len])
    r_smooth, p_smooth = pearson_correlation(smooth_alice, smooth_bob)

    print("\n--- KORELASI PEARSON ---")
    print(f"  Sinyal Mentah  : r = {r_raw:.4f}  (p = {p_raw:.4e})")
    print(f"  Sinyal Halus   : r = {r_smooth:.4f}  (p = {p_smooth:.4e})")
    if r_smooth >= 0.8:
        print("  Interpretasi   : Korelasi KUAT  -> sinyal cocok untuk ekstraksi kunci")
    elif r_smooth >= 0.5:
        print("  Interpretasi   : Korelasi SEDANG -> hasil kunci mungkin ada error")
    else:
        print("  Interpretasi   : Korelasi LEMAH  -> perlu periksa kualitas sinyal")

    # Membuat nama output berdasarkan nama file Alice
    base_name     = os.path.splitext(os.path.basename(file_alice))[0]  # e.g. skenario1alice
    # Hilangkan akhiran 'alice' agar nama lebih bersih
    skenario_name = base_name.replace('alice', '').replace('Alice', '')
    output_csv    = f"Praproses_{skenario_name}.csv"
    output_grafik = f"Grafik_1_ADW_{skenario_name}.png"

    # Menyimpan output dalam bentuk CSV
    pd.DataFrame({
        "smooth_alice": smooth_alice,
        "smooth_bob":   smooth_bob
    }).to_csv(output_csv, index=False)

    # Menjalankan fungsi Plotting
    plot_signal_comparison(raw_alice[:min_len], smooth_alice, output_grafik, limit=150)

    print(f"\nSelesai! Sinyal halus disimpan di : {output_csv}")

if __name__ == "__main__":
    main()
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameter Global Default
INTERVAL_SAMPLING_DETIK = 0.110
MWA_WINDOW_DEFAULT = 20
QUANT_LEVELS_DEFAULT = 16

SEPARATOR = "=" * 65

def cetak_header(judul):
    print(f"\n{SEPARATOR}")
    print(f"  {judul}")
    print(SEPARATOR)

# --- FUNGSI UTILITAS ---
def kgr_bps(jumlah_bit, jumlah_sampel_awal):
    durasi = max(jumlah_sampel_awal * INTERVAL_SAMPLING_DETIK, 1e-9)
    return jumlah_bit / durasi

def quantize(rssi_array, min_val, max_val, levels):
    if max_val == min_val: return np.zeros_like(rssi_array, dtype=int)
    normalized = (rssi_array - min_val) / (max_val - min_val)
    quantized = np.floor(normalized * levels)
    return np.clip(quantized, 0, levels - 1).astype(int)

def binary_to_gray(n, bits):
    gray = int(n) ^ (int(n) >> 1)
    return format(gray, f'0{bits}b')

# --- 1. EKSPERIMEN MWA (PRA-PROSES) ---
def eksperimen_mwa(raw_a, raw_b, window_list, suffix):
    cetak_header(f"EKSPERIMEN 1: Uji Parameter Window Size (MWA) - {suffix.upper()}")
    
    hasil = []
    
    for w in window_list:
        # Terapkan MWA
        mwa_a = pd.Series(raw_a).rolling(window=w).mean().dropna().values
        mwa_b = pd.Series(raw_b).rolling(window=w).mean().dropna().values
        
        n_akhir = min(len(mwa_a), len(mwa_b))
        if n_akhir < 2: 
            continue
            
        mwa_a, mwa_b = mwa_a[:n_akhir], mwa_b[:n_akhir]
        
        # Hitung Korelasi
        corr = pd.Series(mwa_a).corr(pd.Series(mwa_b))
        
        hasil.append({
            'Window Size': w,
            'Pearson Correlation': corr,
            'Remaining Samples': n_akhir
        })
        print(f"  Window: {w:2d} | Correlation: {corr:.4f} | Remaining Samples: {n_akhir}")
        
    df_hasil = pd.DataFrame(hasil)
    
    # Plotting Grafik (Diagram Batang Berdampingan)
    os.makedirs("grafik_scopus", exist_ok=True)
    
    # Treat Window Size as categories for equal spacing
    x_indices = np.arange(len(window_list))
    bar_width = 0.35
    
    fig, ax1 = plt.subplots(figsize=(12, 6.5))
    
    color_corr = '#3498db'  # Elegant Blue
    color_samples = '#e74c3c'  # Elegant Red
    
    ax1.set_xlabel('MWA Window Size (w)', fontweight='bold', fontsize=11, labelpad=10)
    ax1.set_ylabel('Pearson Correlation Coefficient (r)', color=color_corr, fontweight='bold', fontsize=11)
    
    # Batang Kiri: Pearson Correlation (r)
    rects1 = ax1.bar(x_indices - bar_width/2, df_hasil['Pearson Correlation'], bar_width, 
                     label='Pearson Correlation (r)', color=color_corr, alpha=0.85, edgecolor='#2980b9', linewidth=1.2)
    ax1.tick_params(axis='y', labelcolor=color_corr, labelsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5, axis='y')
    ax1.set_ylim(0, 1.15)  # Set limit agar teks di atas batang tidak terpotong
    
    # Tambahkan Sumbu Y kedua untuk Sisa Sampel
    ax2 = ax1.twinx()  
    ax2.set_ylabel('Remaining Samples (N)', color=color_samples, fontweight='bold', fontsize=11)  
    
    # Batang Kanan: Sisa Sampel (N)
    rects2 = ax2.bar(x_indices + bar_width/2, df_hasil['Remaining Samples'], bar_width, 
                     label='Remaining Samples (N)', color=color_samples, alpha=0.85, edgecolor='#c0392b', linewidth=1.2)
    ax2.tick_params(axis='y', labelcolor=color_samples, labelsize=10)
    
    # Set X-tick labels agar rata dan diskrit
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels([str(w) for w in window_list], fontweight='bold', fontsize=10)
    
    # Menggabungkan legend dari kedua sumbu dan menempatkannya di atas grafik
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower center', bbox_to_anchor=(0.5, 1.02),
               ncol=2, shadow=True, fontsize=10, frameon=True)
    
    # Menambahkan anotasi nilai numerik di atas setiap batang
    for rect in rects1:
        height = rect.get_height()
        ax1.annotate(f'{height:.4f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8.5, color='#2980b9', fontweight='bold')
                    
    for rect in rects2:
        height = rect.get_height()
        ax2.annotate(f'{int(height)}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8.5, color='#c0392b', fontweight='bold')
    
    plt.title(f'Influence of MWA Window Size on Pearson Correlation ({suffix.upper()})', fontweight='bold', fontsize=13, pad=35)
    fig.tight_layout()  
    
    file_grafik = f"grafik_scopus/Eksperimen_1_MWA_Tradeoff_{suffix}.png"
    plt.savefig(file_grafik, dpi=300)
    plt.close()
    
    print(f"\n  -> Grafik Eksperimen MWA (Diagram Batang) disimpan di: {file_grafik}")
    return df_hasil

# --- 2. EKSPERIMEN KUANTISASI ---
def eksperimen_kuantisasi(mwa_a, mwa_b, q_list, n_sampel_awal, suffix):
    cetak_header(f"EKSPERIMEN 2: Uji Parameter Kuantisasi (q-levels) - {suffix.upper()}")
    
    hasil = []
    min_rssi = min(np.min(mwa_a), np.min(mwa_b))
    max_rssi = max(np.max(mwa_a), np.max(mwa_b))
    
    for q in q_list:
        num_bits = int(np.log2(q))
        
        # Kuantisasi
        level_a = quantize(mwa_a, min_rssi, max_rssi, q)
        level_b = quantize(mwa_b, min_rssi, max_rssi, q)
        
        # Gray Code
        gray_a_str = [binary_to_gray(val, num_bits) for val in level_a]
        gray_b_str = [binary_to_gray(val, num_bits) for val in level_b]
        
        bit_a_flat = [int(b) for string in gray_a_str for b in string]
        bit_b_flat = [int(b) for string in gray_b_str for b in string]
        
        total_bit = len(bit_a_flat)
        mismatches = sum(a != b for a, b in zip(bit_a_flat, bit_b_flat))
        
        bdr = (mismatches / total_bit) * 100 if total_bit > 0 else 0
        kgr = kgr_bps(total_bit, n_sampel_awal)
        
        hasil.append({
            'Quantization Level (q)': q,
            'BDR (%)': bdr,
            'KGR (bps)': kgr,
            'Total Bits': total_bit
        })
        print(f"  q-level: {q:2d} | BDR: {bdr:5.2f}% | KGR: {kgr:.2f} bps | Total Bits: {total_bit}")

    df_hasil = pd.DataFrame(hasil)
    
    # Plotting Grafik Trade-Off (Diagram Batang Berdampingan)
    os.makedirs("grafik_scopus", exist_ok=True)
    
    # Treat q-levels as categories for equal spacing
    x_indices = np.arange(len(q_list))
    bar_width = 0.35
    
    fig, ax1 = plt.subplots(figsize=(12, 6.5))
    
    # Kustomisasi warna premium
    color_bdr = '#e74c3c'  # Elegant Red
    color_kgr = '#2ecc71'  # Elegant Green
    
    ax1.set_xlabel('Quantization Levels (q)', fontweight='bold', fontsize=11, labelpad=10)
    ax1.set_ylabel('Bit Disagreement Rate / BDR (%)', color=color_bdr, fontweight='bold', fontsize=11)
    
    # Batang Kiri: BDR (%)
    rects1 = ax1.bar(x_indices - bar_width/2, df_hasil['BDR (%)'], bar_width, 
                     label='BDR (%)', color=color_bdr, alpha=0.85, edgecolor='#c0392b', linewidth=1.2)
    ax1.tick_params(axis='y', labelcolor=color_bdr, labelsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5, axis='y')
    
    # Tambahkan Sumbu Y kedua untuk KGR
    ax2 = ax1.twinx()  
    ax2.set_ylabel('Key Generation Rate / KGR (bps)', color=color_kgr, fontweight='bold', fontsize=11)  
    
    # Batang Kanan: KGR (bps)
    rects2 = ax2.bar(x_indices + bar_width/2, df_hasil['KGR (bps)'], bar_width, 
                     label='KGR (bps)', color=color_kgr, alpha=0.85, edgecolor='#27ae60', linewidth=1.2)
    ax2.tick_params(axis='y', labelcolor=color_kgr, labelsize=10)
    
    # Set X-tick labels agar rata dan diskrit
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels([str(q) for q in q_list], fontweight='bold', fontsize=10)
    
    # Menggabungkan legend dari kedua sumbu dan menempatkannya di atas grafik
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower center', bbox_to_anchor=(0.5, 1.02),
               ncol=2, shadow=True, fontsize=10, frameon=True)
    
    # Menambahkan anotasi nilai numerik di atas setiap batang
    for rect in rects1:
        height = rect.get_height()
        ax1.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, color='#c0392b', fontweight='bold')
                    
    for rect in rects2:
        height = rect.get_height()
        ax2.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, color='#27ae60', fontweight='bold')
    
    plt.title(f'Quantization Trade-off Analysis: KGR vs BDR ({suffix.upper()})', fontweight='bold', fontsize=13, pad=35)
    fig.tight_layout()  
    
    file_grafik = f"grafik_scopus/Eksperimen_2_Kuantisasi_Tradeoff_{suffix}.png"
    plt.savefig(file_grafik, dpi=300)
    plt.close()
    
    print(f"\n  -> Grafik Eksperimen Kuantisasi (Diagram Batang) disimpan di: {file_grafik}")
    return df_hasil

# --- EKSEKUSI UTAMA ---
def main():
    print(SEPARATOR)
    print("  SCRIPT EVALUASI PARAMETER (Hyperparameter Tuning) UNTUK SCOPUS")
    print(SEPARATOR)
    
    file_alice = input("Nama file CSV Alice (cth: skenario1alice.csv) : ").strip().strip('"').strip("'")
    file_bob   = input("Nama file CSV Bob   (cth: skenario1bob.csv)   : ").strip().strip('"').strip("'")
    
    if not os.path.exists(file_alice) or not os.path.exists(file_bob):
        print("[ERROR] File tidak ditemukan. Pastikan nama file benar dan ada di folder ini.")
        return

    # Ekstrak nama skenario/suffix dari nama file Alice
    base_name = os.path.basename(file_alice).lower()
    if 'skenario1' in base_name or 'scenario1' in base_name:
        suffix = 'scenario1'
    elif 'skenario2' in base_name or 'scenario2' in base_name:
        suffix = 'scenario2'
    elif 'skenario3' in base_name or 'scenario3' in base_name:
        suffix = 'scenario3'
    else:
        suffix = os.path.splitext(base_name)[0].replace('alice', '').replace(' ', '_').replace('skenario', 'scenario')
        if not suffix:
            suffix = 'scenario_custom'

    # Baca data mentah
    col = 'wlan_radio.signal_dbm'
    df_a = pd.read_csv(file_alice)
    df_b = pd.read_csv(file_bob)
    
    raw_a = df_a[col].dropna().values
    raw_b = df_b[col].dropna().values
    
    n_awal = min(len(raw_a), len(raw_b))
    raw_a, raw_b = raw_a[:n_awal], raw_b[:n_awal]
    
    # 1. Jalankan Eksperimen MWA
    # Menguji Window Size dari 5 hingga 50
    list_window = [5, 10, 15, 20, 25, 30, 40, 50]
    df_mwa = eksperimen_mwa(raw_a, raw_b, list_window, suffix)
    
    # 2. Jalankan Eksperimen Kuantisasi
    # Kita buat kondisi sinyal stabil dengan memakai nilai MWA konstan (default: 20)
    mwa_a_fixed = pd.Series(raw_a).rolling(window=MWA_WINDOW_DEFAULT).mean().dropna().values
    mwa_b_fixed = pd.Series(raw_b).rolling(window=MWA_WINDOW_DEFAULT).mean().dropna().values
    min_len = min(len(mwa_a_fixed), len(mwa_b_fixed))
    mwa_a_fixed, mwa_b_fixed = mwa_a_fixed[:min_len], mwa_b_fixed[:min_len]
    
    # Variasi level kuantisasi (Harus pangkat dari 2 karena kita pakai Gray Code)
    list_q = [2, 4, 8, 16, 32, 64]
    df_q = eksperimen_kuantisasi(mwa_a_fixed, mwa_b_fixed, list_q, n_awal, suffix)
    
    # Simpan tabel hasil dalam CSV agar bisa disalin ke Word / Excel
    df_mwa.to_csv(f"grafik_scopus/Hasil_MWA_{suffix}.csv", index=False)
    df_q.to_csv(f"grafik_scopus/Hasil_Kuantisasi_{suffix}.csv", index=False)
    
    cetak_header("EKSPERIMEN SELESAI")
    print(f"  Tabel data (CSV) dan grafik siap pakai telah disimpan di dalam")
    print(f"  folder 'grafik_scopus/' dengan suffix '_{suffix}'.")
    print(f"  Gunakan grafik resolusi tinggi (300dpi) ini untuk sub-bab jurnal Anda.")

if __name__ == "__main__":
    main()

"""
================================================================================
  pipeline_gabungan.py  —  Automation Pipeline Gabungan
  - Praproses: MWA window=25 (Optimasi Scopus)
  - Kuantisasi: q=8 & Gray Code (Optimasi Scopus)
  - Rekonsiliasi: Cascade Multi-Pass (Jurnal 6)
  - Privacy Amplification: Universal Hash 128 (Proposed)
================================================================================
"""

import os
import sys
import random
import subprocess
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameter Global
INTERVAL_SAMPLING_DETIK = 0.110
MWA_WINDOW = 25
QUANT_LEVELS = 8
CASCADE_MAX_PASSES = 25
CASCADE_INITIAL_BLOCK_SIZE = 4
HASH_BLOCK_SIZE = 128
FILE_HASHTABLE = 'Hashtable128.csv'

SEPARATOR = "=" * 65

def _kgr_bps(jumlah_bit, jumlah_sampel_awal):
    durasi = max(jumlah_sampel_awal * INTERVAL_SAMPLING_DETIK, 1e-9)
    return jumlah_bit / durasi

def _cetak_header(judul):
    print(f"\n{SEPARATOR}")
    print(f"  {judul}")
    print(SEPARATOR)

# --- TAHAP 1: MWA (Jurnal 3) ---
def tahap_praproses_mwa(file_alice, file_bob):
    _cetak_header("TAHAP 1 — Pra-proses (Moving Window Average - Jurnal 3)")
    df_a = pd.read_csv(file_alice)
    df_b = pd.read_csv(file_bob)
    
    col = 'wlan_radio.signal_dbm'
    raw_a = df_a[col].dropna()
    raw_b = df_b[col].dropna()
    
    n_awal = min(len(raw_a), len(raw_b))
    raw_a, raw_b = raw_a[:n_awal], raw_b[:n_awal]
    
    mwa_a = raw_a.rolling(window=MWA_WINDOW).mean().dropna().reset_index(drop=True)
    mwa_b = raw_b.rolling(window=MWA_WINDOW).mean().dropna().reset_index(drop=True)
    
    n_akhir = min(len(mwa_a), len(mwa_b))
    mwa_a, mwa_b = mwa_a[:n_akhir].values, mwa_b[:n_akhir].values
    
    corr_raw = raw_a.corr(raw_b)
    corr_mwa = pd.Series(mwa_a).corr(pd.Series(mwa_b))
    
    print(f"  Jumlah sampel awal      : {n_awal}")
    print(f"  Jumlah sampel setelah MWA: {n_akhir} (Sisa Sampel)")
    print(f"  Korelasi Raw RSSI       : {corr_raw:.4f}")
    print(f"  Korelasi Setelah MWA    : {corr_mwa:.4f}")
    
    return raw_a.values, raw_b.values, mwa_a, mwa_b, n_awal

# --- TAHAP 2: Kuantisasi q=16 & Gray Code (Jurnal 5) ---
def quantize(rssi_array, min_val, max_val, levels):
    if max_val == min_val: return np.zeros_like(rssi_array, dtype=int)
    normalized = (rssi_array - min_val) / (max_val - min_val)
    quantized = np.floor(normalized * levels)
    return np.clip(quantized, 0, levels - 1).astype(int)

def binary_to_gray(n, bits):
    gray = int(n) ^ (int(n) >> 1)
    return format(gray, f'0{bits}b')

def tahap_kuantisasi_jurnal5(mwa_a, mwa_b, n_sampel_awal):
    _cetak_header("TAHAP 2 — Kuantisasi q=16 & Gray Code (Jurnal 5)")
    
    num_bits = int(np.log2(QUANT_LEVELS))
    min_rssi = min(np.min(mwa_a), np.min(mwa_b))
    max_rssi = max(np.max(mwa_a), np.max(mwa_b))
    
    level_a = quantize(mwa_a, min_rssi, max_rssi, QUANT_LEVELS)
    level_b = quantize(mwa_b, min_rssi, max_rssi, QUANT_LEVELS)
    
    gray_a_str = [binary_to_gray(val, num_bits) for val in level_a]
    gray_b_str = [binary_to_gray(val, num_bits) for val in level_b]
    
    bit_a_flat = [int(b) for string in gray_a_str for b in string]
    bit_b_flat = [int(b) for string in gray_b_str for b in string]
    
    total_bit = len(bit_a_flat)
    mismatches = sum(a != b for a, b in zip(bit_a_flat, bit_b_flat))
    bdr = (mismatches / total_bit) * 100 if total_bit > 0 else 0
    kgr = _kgr_bps(total_bit, n_sampel_awal)
    
    print(f"  Total sampel di-kuantisasi : {len(mwa_a)}")
    print(f"  Total bit dihasilkan       : {total_bit} bit (Sisa Bit)")
    print(f"  Mismatch (BDR) Awal        : {bdr:.2f}% ({mismatches} bit beda)")
    print(f"  KGR Tahap Kuantisasi       : {kgr:.4f} bps")
    
    return bit_a_flat, bit_b_flat, kgr, bdr

# --- TAHAP 3: Cascade Multi-Pass (Jurnal 6) ---
def calc_parity(bit_block): 
    return sum(bit_block) % 2

def cascade_binary_search(alice_blk, bob_blk):
    if calc_parity(alice_blk) == calc_parity(bob_blk): return bob_blk.copy()
    if len(alice_blk) == 1: return [1 - bob_blk[0]]
    mid = len(alice_blk) // 2
    if calc_parity(alice_blk[:mid]) != calc_parity(bob_blk[:mid]):
        return cascade_binary_search(alice_blk[:mid], bob_blk[:mid]) + bob_blk[mid:]
    else:
        return bob_blk[:mid] + cascade_binary_search(alice_blk[mid:], bob_blk[mid:])

def cascade_single_pass(a_bits, b_bits, block_size):
    b_corrected = []
    for i in range(0, len(a_bits), block_size):
        b_corrected.extend(cascade_binary_search(a_bits[i:i+block_size], b_bits[i:i+block_size]))
    return b_corrected

def tahap_rekonsiliasi_cascade(alice_bits, bob_bits, n_sampel_awal):
    _cetak_header("TAHAP 3 — Rekonsiliasi Cascade Multi-Pass (Jurnal 6)")
    
    current_bob_bits = bob_bits.copy()
    current_errors = sum(1 for a, b in zip(alice_bits, current_bob_bits) if a != b)
    print(f"  Error Awal (Pra-Cascade) : {current_errors}")
    
    block_size = CASCADE_INITIAL_BLOCK_SIZE
    pass_num = 1
    
    while current_errors > 0 and pass_num <= CASCADE_MAX_PASSES:
        seed = pass_num 
        indices = list(range(len(alice_bits)))
        random.Random(seed).shuffle(indices)
        
        shuffled_alice = [alice_bits[i] for i in indices]
        shuffled_bob = [current_bob_bits[i] for i in indices]
        
        shuffled_bob_corrected = cascade_single_pass(shuffled_alice, shuffled_bob, block_size)
        
        unshuffled_bob = [0] * len(alice_bits)
        for i, original_idx in enumerate(indices):
            unshuffled_bob[original_idx] = shuffled_bob_corrected[i]
        
        current_bob_bits = unshuffled_bob
        current_errors = sum(1 for a, b in zip(alice_bits, current_bob_bits) if a != b)
        
        pass_num += 1
        block_size = min(block_size * 2, len(alice_bits) // 4)
    
    total_bits = len(alice_bits)
    bdr_akhir = (current_errors / total_bits) * 100 if total_bits > 0 else 0
    kgr_rekon = _kgr_bps(total_bits, n_sampel_awal)
    
    print(f"  Pass Selesai             : Pass ke-{pass_num - 1}")
    print(f"  Total bit dihasilkan     : {total_bits} bit (Sisa Bit Tetap)")
    print(f"  Mismatch (BDR) Akhir     : {bdr_akhir:.4f}% ({current_errors} error tersisa)")
    print(f"  KGR Tahap Rekonsiliasi   : {kgr_rekon:.4f} bps")
    
    return alice_bits, current_bob_bits, kgr_rekon, bdr_akhir

# --- TAHAP 4: Privacy Amplification (Universal Hash - Proposed) ---
def apply_universal_hash(bits, hash_matrix):
    bits_np = np.array(bits)
    jumlah_blok = len(bits_np) // HASH_BLOCK_SIZE
    if jumlah_blok == 0: return np.array([])
    
    panjang_valid = jumlah_blok * HASH_BLOCK_SIZE
    bits_terpotong = bits_np[:panjang_valid]
    
    blok_matriks = bits_terpotong.reshape((jumlah_blok, HASH_BLOCK_SIZE))
    hasil_hash = np.dot(blok_matriks, hash_matrix.T) % 2
    return hasil_hash.flatten().tolist()

def tahap_privacy_univhash(bit_a, bit_b_corr, n_sampel_awal, prefix=""):
    _cetak_header("TAHAP 4 — Privacy Amplification (Universal Hash 128)")
    
    file_path = FILE_HASHTABLE
    if not os.path.exists(file_path):
        # try parent directory
        parent_path = os.path.join('..', FILE_HASHTABLE)
        if os.path.exists(parent_path):
            file_path = parent_path
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, FILE_HASHTABLE)
            if not os.path.exists(file_path):
                file_path = os.path.join(script_dir, '..', FILE_HASHTABLE)
                if not os.path.exists(file_path):
                    print(f"  [ERROR] File '{FILE_HASHTABLE}' tidak ditemukan. PA dilewati.")
                    return [], [], 0

    df_h = pd.read_csv(file_path, header=None)
    hash_mat = df_h.to_numpy(dtype=int)
    
    hash_a = apply_universal_hash(bit_a, hash_mat)
    hash_b = apply_universal_hash(bit_b_corr, hash_mat)
    
    mismatch = sum(a != b for a, b in zip(hash_a, hash_b))
    bdr = (mismatch / len(hash_a)) * 100 if len(hash_a) > 0 else 0
    kgr_pa = _kgr_bps(len(hash_a), n_sampel_awal)
    efisiensi = (len(hash_a) / len(bit_a)) * 100 if len(bit_a) > 0 else 0
    
    print(f"  Bit input                : {len(bit_a)}")
    print(f"  Total bit (Terenkripsi)  : {len(hash_a)} bit (Sisa Bit Akhir)")
    print(f"  Efisiensi Retensi        : {efisiensi:.2f}%")
    print(f"  Mismatch Final (BDR)     : {bdr:.2f}% ({mismatch} beda)")
    print(f"  F-KGR (Final KGR)        : {kgr_pa:.4f} bps")
    
    # -------------------------------------------------------------
    # PENYIAPAN FILE UNTUK UJI NIST (Otomatisasi Tahap 5)
    # -------------------------------------------------------------
    if len(hash_a) > 0 and len(hash_b) > 0:
        # File statis untuk .exe
        pd.Series(hash_a).to_csv("Input_NIST_Alice.csv", index=False, header=False)
        pd.Series(hash_b).to_csv("Input_NIST_Bob.csv", index=False, header=False)
        
        # File arsip dengan nama skenario
        if prefix:
            pd.Series(hash_a).to_csv(f"Input_NIST_{prefix}_Alice.csv", index=False, header=False)
            pd.Series(hash_b).to_csv(f"Input_NIST_{prefix}_Bob.csv", index=False, header=False)
            print(f"\n  [INFO NIST] File arsip 'Input_NIST_{prefix}_Alice.csv' telah dibuat.")
            
        print("  [INFO NIST] File 'Input_NIST_Alice.csv' telah siap untuk Uji NIST.")
    
    return hash_a, hash_b, kgr_pa, bdr

# --- TAHAP 5: Uji Keacakan (NIST) ---
def tahap_uji_nist(prefix=""):
    _cetak_header("TAHAP 5 — Uji Keacakan (NIST Test)")
    
    import sys
    exe_name = 'NIST-Test-Alice.exe' if sys.platform.startswith('win') else 'NIST-Test-Alice'
    
    exe_path = exe_name
    if not os.path.exists(exe_path):
        if os.path.exists(os.path.join('..', exe_name)):
            exe_path = os.path.join('..', exe_name)
        else:
            print(f"  [ERROR] File '{exe_name}' tidak ditemukan. Silakan jalankan 'gcc -O3 NIST-Test-Alice.c -o NIST-Test-Alice' di Raspberry Pi terlebih dahulu.")
            return []
            
    print(f"  Menjalankan {os.path.basename(exe_path)} di background...")
    
    input_file = f"Input_NIST_{prefix}_Alice.csv" if prefix else "Input_NIST_Alice.csv"
    if not os.path.exists(input_file):
        input_file = "Input_NIST_Alice.csv"
        
    try:
        # Gunakan path absolut untuk pemanggilan subprocess yang aman
        abs_exe_path = os.path.abspath(exe_path)
        # Menambahkan input newline untuk membypass getchar() pada C, serta operan nama file input
        result = subprocess.run([abs_exe_path, input_file], input=b'\n', cwd='.', capture_output=True)
        if result.returncode != 0:
            print(f"  [ERROR] Biner NIST keluar dengan error code {result.returncode}")
            if result.stderr:
                print(f"  [ERROR] Stderr: {result.stderr.decode(errors='ignore')}")
            if result.stdout:
                print(f"  [ERROR] Stdout: {result.stdout.decode(errors='ignore')}")
    except Exception as e:
        print(f"  [ERROR] Gagal menjalankan NIST: {e}")
        return []
        
    # File output default (bisa 'Alice' jika dicompile lokal, atau 'Bob' jika menggunakan exe bawaan Windows)
    output_nist_default = "sudahujinist_Alice_Sken1.csv"
    if not os.path.exists(output_nist_default):
        output_nist_default = "sudahujinist_Bob_Sken1.csv"
        
    if not os.path.exists(output_nist_default):
        print(f"  [ERROR] File output NIST ('sudahujinist_Alice_Sken1.csv' atau 'sudahujinist_Bob_Sken1.csv') tidak ditemukan.")
        return []
    
    # Buat arsip hasil NIST jika ada prefix
    if prefix:
        import shutil
        output_nist_archive = f"sudahujinist_{prefix}_Alice.csv"
        shutil.copy(output_nist_default, output_nist_archive)
        print(f"  [INFO] Hasil NIST diarsipkan ke '{output_nist_archive}'")
        
    df_indeks = pd.read_csv(output_nist_default, header=None)
    indeks_valid = df_indeks[0].tolist()
    print(f"  Uji NIST selesai! Ditemukan {len(indeks_valid)} blok kunci yang lolos.")
    return indeks_valid


# --- TAHAP 6: Kriptografi Lanjutan (SHA-256 Truncated & AES Key Gen) ---
def tahap_sha_aes(hash_a, hash_b, indeks_valid, n_sampel_awal, prefix=""):
    _cetak_header("TAHAP 6 — Ekstraksi Kunci Final (SHA-256 Truncated & AES-128)")
    
    if not indeks_valid:
        print("  [Peringatan] Tidak ada blok yang lolos uji NIST untuk diekstrak.")
        return 0, 0
        
    hash_a_np = np.array(hash_a)
    hash_b_np = np.array(hash_b)
    
    kunci_cocok = 0
    kunci_aes_list = []
    
    for idx in indeks_valid:
        start = idx * HASH_BLOCK_SIZE
        end = start + HASH_BLOCK_SIZE
        if end > len(hash_a_np):
            continue
            
        blok_a = hash_a_np[start:end]
        blok_b = hash_b_np[start:end]
        
        str_a = "".join(str(e) for e in blok_a)
        str_b = "".join(str(e) for e in blok_b)
        
        sha_a = hashlib.sha256(str_a.encode('ascii')).hexdigest()[:32]
        sha_b = hashlib.sha256(str_b.encode('ascii')).hexdigest()[:32]
        
        if sha_a == sha_b:
            kunci_cocok += 1
            # Konversi string binary 128 bit menjadi AES Hex Key
            keyint = int(str_a, 2)
            hex_str = '%x' % keyint
            if len(hex_str) % 2 != 0:
                hex_str = '0' + hex_str
            kunci_aes_list.append(hex_str)
            
    final_bits = kunci_cocok * 128
    final_kgr = _kgr_bps(final_bits, n_sampel_awal)
    
    print(f"  Blok dienkripsi SHA-256  : {len(indeks_valid)} blok")
    print(f"  Kunci AES Terverifikasi  : {kunci_cocok} Kunci (cocok antara Alice & Bob)")
    print(f"  Total Bit Kunci (Murni)  : {final_bits} bit")
    print(f"  * FINAL KGR (AES)        : {final_kgr:.4f} bps")
    
    if kunci_aes_list:
        os.makedirs("key", exist_ok=True)
        filename_txt = f"Final_AES_{prefix}.txt" if prefix else "Final_AES_Keys.txt"
        file_path = os.path.join("key", filename_txt)
        with open(file_path, "w") as f:
            for i, h in enumerate(kunci_aes_list):
                f.write(f"Key-{i+1} : {h}\n")
        print(f"\n  [INFO] Kunci rahasia Hexadecimal (AES) telah disimpan di:")
        print(f"         '{file_path}'")
        
    return final_kgr, final_bits


# --- MAIN EXECUTOR ---
def main():
    print(SEPARATOR)
    print(f"  PIPELINE GABUNGAN: MWA (w={MWA_WINDOW}) + Kuantisasi q={QUANT_LEVELS} + Cascade + UnivHash")
    print(SEPARATOR)
    
    file_alice = input("Nama file CSV Alice (cth: skenario1alice.csv) : ").strip().strip('"').strip("'")
    file_bob   = input("Nama file CSV Bob   (cth: skenario1bob.csv)   : ").strip().strip('"').strip("'")
    
    # Check current dir
    for f in [file_alice, file_bob]:
        f_path = f
        if not os.path.exists(f_path):
            if os.path.exists(os.path.join('..', f)):
                pass
            else:
                print(f"[ERROR] File '{f}' tidak ditemukan di working directory saat ini.")
                sys.exit(1)
                
    # Re-assign if in parent dir
    if not os.path.exists(file_alice):
        file_alice = os.path.join('..', file_alice)
    if not os.path.exists(file_bob):
        file_bob = os.path.join('..', file_bob)
            
    # Deteksi nama skenario dari input (misal: skenario1alice.csv -> skenario1)
    prefix = ""
    if "skenario" in file_alice.lower():
        # Cari angka setelah kata skenario
        import re
        match = re.search(r'(skenario\d+)', file_alice.lower())
        if match:
            prefix = match.group(1)
            
    import time

    t_start = time.perf_counter()
    raw_a, raw_b, mwa_a, mwa_b, n_awal = tahap_praproses_mwa(file_alice, file_bob)
    t_pra = time.perf_counter() - t_start

    t_start = time.perf_counter()
    bit_a, bit_b, kgr_q, bdr_q = tahap_kuantisasi_jurnal5(mwa_a, mwa_b, n_awal)
    t_kuan = time.perf_counter() - t_start

    t_start = time.perf_counter()
    bit_a_fin, bit_b_corr, kgr_r, bdr_r = tahap_rekonsiliasi_cascade(bit_a, bit_b, n_awal)
    t_rekon = time.perf_counter() - t_start

    t_start = time.perf_counter()
    hash_a, hash_b, _, bdr_pa = tahap_privacy_univhash(bit_a_fin, bit_b_corr, n_awal, prefix=prefix)
    t_pa = time.perf_counter() - t_start

    t_start = time.perf_counter()
    indeks_valid = tahap_uji_nist(prefix=prefix)
    t_nist = time.perf_counter() - t_start

    t_start = time.perf_counter()
    f_kgr_aes, final_bits = tahap_sha_aes(hash_a, hash_b, indeks_valid, n_awal, prefix=prefix)
    t_aes = time.perf_counter() - t_start

    # Uji NIST adalah validasi, tidak dimasukkan dalam beban waktu algoritma runtime
    t_algo_komputasi = t_pra + t_kuan + t_rekon + t_pa + t_aes
    t_total_keseluruhan = t_algo_komputasi + t_nist
    
    durasi_fisik = n_awal * INTERVAL_SAMPLING_DETIK
    waktu_total_end_to_end = durasi_fisik + t_algo_komputasi
    f_kgr_total = final_bits / waktu_total_end_to_end if waktu_total_end_to_end > 0 else 0

    _cetak_header("RINGKASAN AKHIR PIPELINE GABUNGAN (FULL AUTOMATION)")
    print(f"  Total Waktu Akuisisi Fisik : {durasi_fisik:.1f} detik")
    print(f"  KGR Kuantisasi             : {kgr_q:.4f} bps")
    print(f"  KGR Rekonsiliasi           : {kgr_r:.4f} bps")
    print(f"  * TOTAL KGR (End-to-End)   : {f_kgr_total:.4f} bps")

    print(SEPARATOR)
    print("  DURASI EKSEKUSI KOMPUTASI CPU:")
    print(f"  - Praproses MWA            : {t_pra:.6f} s")
    print(f"  - Kuantisasi               : {t_kuan:.6f} s")
    print(f"  - Rekonsiliasi Cascade     : {t_rekon:.6f} s")
    
    t_pa_total = t_pa + t_aes
    print(f"  - Privacy Amplification    : {t_pa_total:.6f} s (UnivHash + SHA-256 + AES)")
    print(f"  -------------------------------------------------")
    print(f"  * TOTAL WAKTU ALGORITMA    : {t_algo_komputasi:.6f} s")
    print(f"  - Waktu Validasi NIST      : {t_nist:.6f} s (Eksternal, tidak dihitung di KGR)")
    print(f"  * TOTAL WAKTU KESELURUHAN  : {t_total_keseluruhan:.6f} s")
    
    # Simpan kunci final ke CSV untuk pembuktian validasi
    output_csv = f"KunciFinal_{prefix}.csv" if prefix else "Kunci_Final_Gabungan.csv"
    pd.DataFrame({
        "Kunci_Alice": hash_a,
        "Kunci_Bob": hash_b
    }).to_csv(output_csv, index=False)
    print(f"\n  [INFO] Kunci final telah disimpan di '{output_csv}'")
    print(f"         Anda bisa membuka file tersebut untuk memvalidasi bahwa kunci mereka 100% identik.")
    
    # --- VISUALISASI AKHIR ---
    _visualisasi_final(
        raw_a, raw_b, mwa_a, mwa_b, 
        bit_a, bit_b, bit_b_corr, 
        hash_a, hash_b, prefix, 
        kgr_q, kgr_r, f_kgr_aes,
        bdr_q, bdr_r, bdr_pa
    )
    
    print(SEPARATOR)

def _visualisasi_final(raw_a, raw_b, mwa_a, mwa_b, bit_a, bit_b, bit_b_corr, hash_a, hash_b, prefix, kgr_q, kgr_r, f_kgr_aes, bdr_q, bdr_r, bdr_pa):
    """Internal function to generate plots for each stage."""
    os.makedirs("plots", exist_ok=True)
    
    # 1. MWA RSSI Plot (Before and After)
    plt.figure(figsize=(12, 6))
    
    # Before Preprocessing
    plt.subplot(2, 1, 1)
    plt.plot(raw_a[:200], label='Alice Raw', color='#4C72B0', alpha=0.6)
    plt.plot(raw_b[:200], label='Bob Raw', color='#C44E52', linestyle='--', alpha=0.6)
    plt.title(f"Before Preprocessing: Raw RSSI Signal ({prefix})")
    plt.ylabel("RSSI (dBm)")
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    
    # After Preprocessing (MWA)
    plt.subplot(2, 1, 2)
    plt.plot(mwa_a[:200], label='Alice MWA', color='#4C72B0', linewidth=1.5)
    plt.plot(mwa_b[:200], label='Bob MWA', color='#C44E52', linestyle='--', linewidth=1.5)
    plt.title(f"After Preprocessing: MWA Smoothed Signal ({prefix})")
    plt.xlabel("Sample Index")
    plt.ylabel("RSSI (dBm)")
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"plots/1_MWA_{prefix}.png", dpi=300)
    plt.close()

    # 2. Quantization Bits Plot (Before and After)
    plt.figure(figsize=(12, 6))
    
    # Before Quantization (Analog MWA Signal)
    plt.subplot(2, 1, 1)
    plt.plot(mwa_a[:200], color='#4C72B0', linewidth=1.5, label='Alice MWA')
    plt.title(f"Before Quantization: Analog RSSI Signal ({prefix})")
    plt.ylabel("RSSI (dBm)")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")
    
    # After Quantization (Barcode Bits)
    plt.subplot(2, 1, 2)
    barcode_data = np.array(bit_a[:200]).reshape(1, -1)
    plt.imshow(barcode_data, cmap='binary', aspect='auto', extent=[0, 200, 0, 1])
    plt.title(f"After Quantization: Digital Bitstream Barcode (q={QUANT_LEVELS}) ({prefix})")
    plt.xlabel("Bit Index (First 200 Bits)")
    plt.yticks([]) # hide y-axis ticks
    
    plt.tight_layout()
    plt.savefig(f"plots/2_Quantization_{prefix}.png", dpi=300)
    plt.close()

    # 3. Reconciliation Mismatch Plot (Before and After)
    plt.figure(figsize=(12, 6))
    
    # Before Reconciliation
    diff_before = [1 if a != b else 0 for a, b in zip(bit_a[:200], bit_b[:200])]
    plt.subplot(2, 1, 1)
    markerline1, stemlines1, baseline1 = plt.stem(range(len(diff_before)), diff_before, linefmt='#C44E52', markerfmt='ro', basefmt='k-')
    plt.setp(baseline1, color='black', linewidth=1)
    plt.title(f"Before Reconciliation: Initial Bit Mismatches ({prefix})")
    plt.ylabel("Mismatch")
    plt.yticks([0, 1], ['Match (0)', 'Mismatch (1)'])
    plt.ylim(-0.2, 1.2)
    plt.grid(True, alpha=0.3, axis='x')
    
    # After Reconciliation
    diff_after = [1 if a != b else 0 for a, b in zip(bit_a[:200], bit_b_corr[:200])]
    plt.subplot(2, 1, 2)
    markerline2, stemlines2, baseline2 = plt.stem(range(len(diff_after)), diff_after, linefmt='#55A868', markerfmt='go', basefmt='k-')
    plt.setp(baseline2, color='black', linewidth=1)
    plt.title(f"After Reconciliation: Corrected Bit Mismatches ({prefix})")
    plt.xlabel("Bit Index (First 200 Bits)")
    plt.ylabel("Mismatch")
    plt.yticks([0, 1], ['Match (0)', 'Mismatch (1)'])
    plt.ylim(-0.2, 1.2)
    plt.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(f"plots/3_Reconciliation_{prefix}.png", dpi=300)
    plt.close()

    # 4. Final Key Bit Map (Before and After Privacy Amplification)
    if len(hash_a) > 0 and len(bit_a) > 0:
        plt.figure(figsize=(10, 5))
        
        # Before PA (Reconciled Bits)
        plt.subplot(1, 2, 1)
        side1 = int(np.sqrt(len(bit_a)))
        if side1 * side1 < len(bit_a): side1 += 1
        pad1 = bit_a + [0]*(side1*side1 - len(bit_a))
        plt.imshow(np.array(pad1).reshape((side1, side1)), cmap='binary', interpolation='nearest')
        plt.title(f"Before PA: Reconciled Key Bit Map ({prefix})")
        plt.axis('off')
        
        # After PA (Hashed Bits)
        plt.subplot(1, 2, 2)
        side2 = int(np.sqrt(len(hash_a)))
        if side2 * side2 < len(hash_a): side2 += 1
        pad2 = hash_a + [0]*(side2*side2 - len(hash_a))
        plt.imshow(np.array(pad2).reshape((side2, side2)), cmap='binary', interpolation='nearest')
        plt.title(f"After PA: Final Secret Key Bit Map ({prefix})")
        plt.axis('off')
        
        plt.tight_layout()
        plt.savefig(f"plots/4_PrivacyAmplification_{prefix}.png", dpi=300)
        plt.close()
    
    # 5. Performance Metrics (BDR and KGR Before and After)
    plt.figure(figsize=(12, 6))
    
    # BDR Performance
    plt.subplot(1, 2, 1)
    bdr_stages = ['Quantization', 'Reconciliation', 'Privacy Amp']
    bdr_values = [bdr_q, bdr_r, bdr_pa]
    plt.plot(bdr_stages, bdr_values, marker='o', color='#C44E52', linewidth=2, markersize=8)
    for i, v in enumerate(bdr_values):
        plt.text(i, v + (max(bdr_values)*0.05), f"{v:.2f}%", ha='center', fontweight='bold')
    plt.title(f"Bit Disagreement Rate (BDR) Progression ({prefix})")
    plt.ylabel("BDR (%)")
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max(bdr_values) * 1.2 if max(bdr_values) > 0 else 10)
    
    # KGR Performance
    plt.subplot(1, 2, 2)
    kgr_stages = ['Quantization', 'Reconciliation', 'Final (AES)']
    kgr_values = [kgr_q, kgr_r, f_kgr_aes]
    bars = plt.bar(kgr_stages, kgr_values, color=['#4C72B0', '#55A868', '#DD8452'], edgecolor='black', alpha=0.8)
    plt.title(f"Key Generation Rate (KGR) Drops ({prefix})")
    plt.ylabel("KGR (bps)")
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    max_kgr = max(kgr_values) if max(kgr_values) > 0 else 1
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02 * max_kgr, f"{yval:.2f}", ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(f"plots/5_Performance_Metrics_{prefix}.png", dpi=300)
    plt.close()
    
    print(f"  [INFO GRAPH] 5 plots have been saved to the 'plots/' directory.")

if __name__ == "__main__":
    main()

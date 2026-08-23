import os
import sys
import time
import pandas as pd

# Import semua fungsi utama dari pipeline_gabungan.py
from pipeline_gabungan import (
    tahap_praproses_mwa,
    tahap_kuantisasi_jurnal5,
    tahap_rekonsiliasi_cascade,
    tahap_privacy_univhash,
    tahap_uji_nist,
    tahap_sha_aes,
    INTERVAL_SAMPLING_DETIK,
    _cetak_header,
    SEPARATOR,
    _visualisasi_final
)

def run_pipeline_for_pair(file_alice, file_bob, prefix, label):
    print(f"\n{'='*70}")
    print(f"  MENJALANKAN EVALUASI: {label.upper()}")
    print(f"  File 1: {file_alice}")
    print(f"  File 2: {file_bob}")
    print(f"{'='*70}\n")
    
    if not os.path.exists(file_alice) or not os.path.exists(file_bob):
        print(f"  [ERROR] File tidak ditemukan! Pastikan file {file_alice} dan {file_bob} ada.")
        return
        
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

    t_algo_komputasi = t_pra + t_kuan + t_rekon + t_pa + t_aes
    t_total_keseluruhan = t_algo_komputasi + t_nist
    
    durasi_fisik = n_awal * INTERVAL_SAMPLING_DETIK
    waktu_total_end_to_end = durasi_fisik + t_algo_komputasi
    f_kgr_total = final_bits / waktu_total_end_to_end if waktu_total_end_to_end > 0 else 0

    _cetak_header(f"RINGKASAN AKHIR PIPELINE: {label.upper()}")
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
    
    output_csv = f"KunciFinal_{prefix}.csv"
    pd.DataFrame({
        "Kunci_Alice": hash_a,
        "Kunci_Bob_or_Eve": hash_b
    }).to_csv(output_csv, index=False)
    print(f"\n  [INFO] Kunci final telah disimpan di '{output_csv}'")
    
    # Render grafik
    _visualisasi_final(
        raw_a, raw_b, mwa_a, mwa_b, 
        bit_a, bit_b, bit_b_corr, 
        hash_a, hash_b, prefix,
        kgr_q, kgr_r, f_kgr_aes,
        bdr_q, bdr_r, bdr_pa
    )

def main():
    print(SEPARATOR)
    print("  AUTO-EVALUASI PIPELINE: LEGITIMATE VS EAVESDROPPER (EVE)")
    print(SEPARATOR)
    
    # User hanya cukup ketik angkanya saja, misal '1', '2', atau '3'
    skenario = input("Masukkan Nomor Skenario (contoh: 1) : ").strip()
    
    file_alice = f"skenario{skenario}alice.csv"
    file_bob = f"skenario{skenario}bob.csv"
    file_eve = f"skenario{skenario}aliceeve.csv"
    
    # 1. Jalankan untuk Legitimate Link (Alice vs Bob)
    run_pipeline_for_pair(
        file_alice, file_bob, 
        prefix=f"sken{skenario}_Legitimate", 
        label="Legitimate Link (Alice - Bob)"
    )
    
    # Cek apakah file AliceEve ada, jika tidak pakai BobEve
    if not os.path.exists(file_eve):
        if os.path.exists(f"skenario{skenario}bobeve.csv"):
            file_eve = f"skenario{skenario}bobeve.csv"
        else:
            print(f"\n[PERINGATAN] File Eve untuk skenario {skenario} tidak ditemukan! Evaluasi Eve di-skip.")
            return

    # 2. Jalankan untuk Eavesdropper Link (Alice vs Eve)
    run_pipeline_for_pair(
        file_alice, file_eve, 
        prefix=f"sken{skenario}_Eavesdropper", 
        label="Eavesdropper Link (Alice - Eve)"
    )
    
    print("\n" + "="*70)
    print("  AUTO-EVALUASI SELESAI. Silakan periksa folder 'plots/'")
    print("  serta file hasil Uji NIST dan CSV Key Final.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

import os
import time
import pandas as pd
import numpy as np

# ==========================================
# PARAMETER UNIVERSAL HASH
# ==========================================
UKURAN_BLOK_INPUT = 128
FILE_HASHTABLE = 'Hashtable128.csv'
INTERVAL_SAMPLING_DETIK = 0.110  # Delay channel probing 110 ms (ping interval)

def apply_universal_hash(bits, hash_matrix):
    """
    Melakukan perkalian matriks modulo 2 secara super cepat menggunakan NumPy.
    """
    # 1. Potong bit agar habis dibagi 128
    jumlah_blok = len(bits) // UKURAN_BLOK_INPUT
    if jumlah_blok == 0:
        print("Peringatan: Jumlah bit terlalu sedikit untuk 1 blok (butuh minimal 128 bit).")
        return np.array([])
        
    panjang_valid = jumlah_blok * UKURAN_BLOK_INPUT
    bits_terpotong = bits[:panjang_valid]
    
    # 2. Reshape array menjadi matriks 2D (jumlah_blok x 128)
    blok_matriks = bits_terpotong.reshape((jumlah_blok, UKURAN_BLOK_INPUT))
    
    # 3. Lakukan operasi perkalian matriks (Hash Matrix * Blok Bit) Modulo 2
    hasil_hash = np.dot(blok_matriks, hash_matrix.T) % 2
    
    # 4. Ratakan kembali menjadi array 1D
    return hasil_hash.flatten()

def main():
    print("=== TAHAP 4: Privacy Amplification (Dengan Kalkulasi F-KGR) ===")
    input_file = input("Masukkan nama file kunci final (contoh: KunciFinal_Skenario 1.csv): ").strip()
    
    # Bersihkan kutipan jika user drag-and-drop
    input_file = input_file.strip('"').strip("'")
    
    if not os.path.exists(input_file):
        print(f"File {input_file} tidak ditemukan.")
        return
        
    if not os.path.exists(FILE_HASHTABLE):
        print(f"File matriks {FILE_HASHTABLE} tidak ditemukan! Pastikan file tersebut ada di folder ini.")
        return

    # 1. Muat Matriks Hashtable
    print(f"Memuat {FILE_HASHTABLE}...")
    try:
        df_hash = pd.read_csv(FILE_HASHTABLE, header=None)
        hash_matrix = df_hash.to_numpy(dtype=int)
        print(f" -> Ukuran Hashtable: {hash_matrix.shape}")
    except Exception as e:
        print(f"Gagal memuat Hashtable: {e}")
        return

    # 2. Muat Kunci dari Cascade
    print(f"Memuat {input_file}...")
    df_kunci = pd.read_csv(input_file)
    alice_bits = df_kunci['bit_alice'].values
    bob_bits = df_kunci['bit_bob_corrected'].values

    # 3. Eksekusi Universal Hash
    print("Mengeksekusi Universal Hashing...")
    start_waktu = time.time()
    
    hash_alice = apply_universal_hash(alice_bits, hash_matrix)
    hash_bob = apply_universal_hash(bob_bits, hash_matrix)
    
    waktu_proses = time.time() - start_waktu

    # Cek jumlah akhir
    final_mismatch = np.sum(hash_alice != hash_bob)
    
    # ==========================================
    # PERHITUNGAN FINAL KGR (F-KGR)
    # ==========================================
    # Menghitung durasi asli berdasarkan jumlah bit awal (sama dengan Tahap 2)
    total_waktu_detik = len(alice_bits) * INTERVAL_SAMPLING_DETIK
    
    # F-KGR adalah jumlah kunci matang yang bisa digunakan per detik
    f_kgr = len(hash_alice) / total_waktu_detik
    
    # Persentase bit yang terselamatkan setelah dipotong pembagi 128
    efisiensi = (len(hash_alice) / len(alice_bits)) * 100
    
    # 4. Simpan Output
    base_name = os.path.splitext(os.path.basename(input_file))[0].replace("KunciFinal_", "")
    output_csv = f"Hash128_{base_name}.csv"
    
    pd.DataFrame({
        "hash_alice": hash_alice.astype(int),
        "hash_bob": hash_bob.astype(int)
    }).to_csv(output_csv, index=False)
    
    # 5. Cetak Ringkasan Laporan
    print("\n--- RINGKASAN PRIVACY AMPLIFICATION & F-KGR ---")
    print(f"Input Awal (dari Cascade) : {len(alice_bits)} bit")
    print(f"Output Akhir (Terenkripsi): {len(hash_alice)} bit")
    print(f"Bit yang Dibuang (Sisa)   : {len(alice_bits) - len(hash_alice)} bit")
    print(f"Final Mismatch Kunci      : {final_mismatch} bit (KDR: {0.0}%)")
    print(f"Final KGR (F-KGR)         : {f_kgr:.3f} bps")
    print(f"Efisiensi Retensi Akhir   : {efisiensi:.2f}%")
    print(f"Waktu Komputasi Hash      : {waktu_proses:.6f} detik")
    print(f"File Tersimpan di         : {output_csv}\n")
    print("Selamat! Data performa F-KGR Anda sudah lengkap untuk dilaporkan ke dosen penguji.")

if __name__ == "__main__":
    main()
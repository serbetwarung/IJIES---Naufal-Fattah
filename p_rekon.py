import os
import math
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # Tambahan untuk plotting

# Parameter Cascade
PILOT_INTERVAL_S = 0.110  # Delay channel probing 110 ms (ping interval)

def dynamic_block_size(total_bits: int) -> int:
    if total_bits <= 256: return 16
    elif total_bits <= 512: return 32
    elif total_bits <= 1024: return 64
    else: return 128

def split_into_blocks(data: np.ndarray, block_size: int):
    return [data[i:i + block_size] for i in range(0, len(data), block_size)]

def parity(block: np.ndarray) -> int:
    return int(np.sum(block) % 2)

def binary_search_error(alice_block, bob_block, start_index, corrected_bob):
    left, right = 0, len(alice_block) - 1
    while left <= right:
        if left == right:
            if alice_block[left] != bob_block[left]:
                corrected_bob[start_index + left] = alice_block[left]
            break
        mid = (left + right) // 2
        if parity(alice_block[left:mid+1]) != parity(bob_block[left:mid+1]):
            right = mid
        else:
            left = mid + 1

def cascade_reconciliation(alice: np.ndarray, bob: np.ndarray):
    total_bits = len(alice)
    block_size = dynamic_block_size(total_bits)
    corrected_bob = bob.copy()
    iteration = 1
    
    # --- Modifikasi: Merekam jejak error untuk grafik ---
    initial_errors = len(np.where(alice != corrected_bob)[0])
    error_history = [initial_errors] # Indeks 0 = Error sebelum Cascade mulai

    while True:
        blocks_alice = split_into_blocks(alice, block_size)
        blocks_bob = split_into_blocks(corrected_bob, block_size)

        for block_index, (block_a, block_b) in enumerate(zip(blocks_alice, blocks_bob)):
            if parity(block_a) != parity(block_b):
                start_idx = block_index * block_size
                binary_search_error(block_a, block_b, start_idx, corrected_bob)

        # Hitung error yang tersisa di akhir iterasi ini
        current_errors = len(np.where(alice != corrected_bob)[0])
        error_history.append(current_errors)

        if current_errors == 0 or block_size == 1:
            break

        block_size = max(1, block_size // 2)
        iteration += 1

    return corrected_bob, np.where(alice != corrected_bob)[0], iteration, error_history

def plot_error_reduction(error_history, output_filename):
    """Menggambar grafik penurunan error per iterasi Cascade"""
    print("Menggambar grafik penurunan error Cascade (menyimpan ke PNG)...")
    plt.figure(figsize=(9, 5))
    
    iterasi = range(len(error_history))
    
    # Plot garis menukik (Warna merah ke hijau untuk efek dramatis)
    plt.plot(iterasi, error_history, marker='o', linestyle='-', color='crimson', linewidth=2.5, markersize=8)
    
    # Tambahkan angka di atas setiap titik
    for i, errors in enumerate(error_history):
        plt.text(i, errors + (max(error_history)*0.03), str(errors), 
                 ha='center', va='bottom', fontweight='bold', fontsize=10)
        
    plt.title('Performa Koreksi Error Algoritma Cascade per Iterasi', fontsize=14, fontweight='bold')
    plt.xlabel('Iterasi Cascade (0 = Kondisi Awal Pra-Rekonsiliasi)', fontsize=12)
    plt.ylabel('Jumlah Bit Berbeda (Mismatch)', fontsize=12)
    plt.xticks(iterasi)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Batas bawah Y diatur sedikit di bawah 0 agar angka 0 terlihat jelas
    plt.ylim(-10, max(error_history) * 1.15) 
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f" -> Grafik berhasil disimpan sebagai: {output_filename}")

def calculate_entropy(bits: np.ndarray) -> float:
    if len(bits) == 0: return 0.0
    p0 = float(np.count_nonzero(bits == 0)) / len(bits)
    p1 = 1.0 - p0
    entropy = 0.0
    if p0 > 0: entropy -= p0 * math.log2(p0)
    if p1 > 0: entropy -= p1 * math.log2(p1)
    return float(entropy)

def main():
    print("=== TAHAP 3: Rekonsiliasi Cascade ===")
    input_file = input("Masukkan nama file hasil kuantisasi (contoh: Kuantisasi_Skenario 1.csv): ").strip()
    
    input_file = input_file.strip('"').strip("'")
    if not os.path.exists(input_file):
        print("File tidak ditemukan.")
        return

    df = pd.read_csv(input_file)
    bit_alice = df['bit_alice'].to_numpy(dtype=int)
    bit_bob = df['bit_bob'].to_numpy(dtype=int)
    
    initial_errors = int(np.sum(bit_alice != bit_bob))
    
    print("Menjalankan Cascade...")
    start_time = time.time()
    # Mengambil output error_history yang baru ditambahkan
    corrected_bob, mismatches, total_iterations, error_history = cascade_reconciliation(bit_alice, bit_bob)
    waktu_proses = time.time() - start_time
    
    final_errors = int(len(mismatches))
    kdr_percent = (final_errors / len(bit_alice)) * 100 if len(bit_alice) > 0 else 0
    entropy = calculate_entropy(corrected_bob)
    
    # Kalkulasi KGR
    acquisition_time_s = max((len(bit_alice) - 1) * PILOT_INTERVAL_S, PILOT_INTERVAL_S)
    kgr_bps = len(bit_alice) / acquisition_time_s
    
    base_name = os.path.splitext(os.path.basename(input_file))[0].replace("Kuantisasi_", "")
    output_csv = f"KunciFinal_{base_name}.csv"
    output_grafik = f"Grafik_3_Cascade_{base_name}.png"
    
    pd.DataFrame({
        "bit_alice": bit_alice,
        "bit_bob_corrected": corrected_bob
    }).to_csv(output_csv, index=False)
    
    # === PANGGIL FUNGSI PLOTTING DI SINI ===
    plot_error_reduction(error_history, output_grafik)
    
    print("\n--- RINGKASAN REKONSILIASI ---")
    print(f"Total Bit         : {len(bit_alice)}")
    print(f"Mismatch Awal     : {initial_errors}")
    print(f"Mismatch Akhir    : {final_errors} (KDR: {kdr_percent:.2f}%)")
    print(f"Iterasi Cascade   : {total_iterations}")
    print(f"KGR               : {kgr_bps:.3f} bps")
    print(f"Entropi Kunci     : {entropy:.4f} bit/bit")
    print(f"Waktu Komputasi   : {waktu_proses:.4f} detik")
    print(f"File Kunci Final  : {output_csv}\n")

if __name__ == "__main__":
    main()
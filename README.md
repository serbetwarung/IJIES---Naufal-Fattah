# IJIES - Naufal Fattah

Repository ini berisi implementasi eksperimen Secret Key Generation (SKG) berbasis RSSI untuk kebutuhan penelitian/tesis. Pipeline utama menggabungkan beberapa tahap: pra-proses Moving Window Average (MWA), kuantisasi Gray Code, rekonsiliasi Cascade Multi-Pass, privacy amplification dengan Universal Hash, validasi NIST, dan ekstraksi kunci AES-128.

## Struktur Kode

| File | Keterangan |
| --- | --- |
| `pipeline_gabungan.py` | Pipeline utama end-to-end untuk Alice dan Bob. |
| `pipeline_auto_evalwitheve.py` | Evaluasi otomatis legitimate link dan eavesdropper/Eve berdasarkan nomor skenario. |
| `eksperimen_scopus.py` | Eksperimen parameter MWA dan kuantisasi untuk analisis trade-off. |
| `p_pra.py` | Tahap pra-proses RSSI. |
| `p_kuan.py` | Tahap kuantisasi. |
| `p_rekon.py` | Tahap rekonsiliasi. |
| `p_univhash.py` | Tahap privacy amplification Universal Hash. |
| `plot_*.py`, `*_gambar.py`, `kgrvsbmr.py` | Script visualisasi/grafik pendukung artikel/tesis. |

## Tahapan Pipeline

1. **Pra-proses RSSI**
   - Membaca file CSV Alice dan Bob.
   - Menggunakan kolom `wlan_radio.signal_dbm`.
   - Melakukan smoothing dengan Moving Window Average.

2. **Kuantisasi**
   - Mengubah RSSI hasil MWA menjadi level kuantisasi.
   - Mengonversi level menjadi bit menggunakan Gray Code.
   - Menghitung BDR dan KGR awal.

3. **Rekonsiliasi**
   - Menggunakan Cascade Multi-Pass untuk menurunkan mismatch bit antara Alice dan Bob.

4. **Privacy Amplification**
   - Menggunakan matriks Universal Hash 128-bit dari `Hashtable128.csv`.
   - Menghasilkan bit kunci akhir dan file input untuk uji NIST.

5. **Uji NIST dan Ekstraksi AES**
   - Menjalankan biner `NIST-Test-Alice.exe` pada Windows atau `NIST-Test-Alice` pada Linux/Raspberry Pi.
   - Mengambil blok yang lolos validasi.
   - Menghasilkan kunci AES-128 dalam format heksadesimal.

## Kebutuhan Sistem

- Python 3.10 atau lebih baru
- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `PyWavelets`
- Biner/source NIST test untuk tahap validasi keacakan

Install dependensi Python:

```bash
pip install -r requirements.txt
```

## File Data yang Diperlukan

Pipeline utama membutuhkan file berikut di working directory atau satu level di atasnya:

- `Hashtable128.csv`
- `skenario1alice.csv`, `skenario1bob.csv`
- `skenario2alice.csv`, `skenario2bob.csv`
- `skenario3alice.csv`, `skenario3bob.csv`
- Opsional untuk evaluasi Eve:
  - `skenario1aliceeve.csv` atau `skenario1bobeve.csv`
  - `skenario2aliceeve.csv` atau `skenario2bobeve.csv`
  - `skenario3aliceeve.csv` atau `skenario3bobeve.csv`
- Untuk NIST:
  - Windows: `NIST-Test-Alice.exe`
  - Linux/Raspberry Pi: `NIST-Test-Alice`

## Cara Menjalankan

Jalankan pipeline utama:

```bash
python pipeline_gabungan.py
```

Masukkan nama file CSV saat diminta, contoh:

```text
skenario1alice.csv
skenario1bob.csv
```

Jalankan evaluasi otomatis legitimate vs eavesdropper:

```bash
python pipeline_auto_evalwitheve.py
```

Masukkan nomor skenario saat diminta, contoh:

```text
1
```

## Output

Output yang dihasilkan dapat berupa:

- `KunciFinal_*.csv`
- `Input_NIST_*.csv`
- `sudahujinist_*.csv`
- `key/Final_AES_*.txt`
- `plots/*.png`
- `grafik_scopus/*.png`
- `output_images/*.png`

File output eksperimen dan validasi tidak disarankan untuk dilacak Git kecuali memang dibutuhkan sebagai artefak penelitian.

## Catatan Reproduksibilitas

Nilai parameter utama berada di `pipeline_gabungan.py`:

```python
INTERVAL_SAMPLING_DETIK = 0.110
MWA_WINDOW = 25
QUANT_LEVELS = 8
CASCADE_MAX_PASSES = 25
CASCADE_INITIAL_BLOCK_SIZE = 4
HASH_BLOCK_SIZE = 128
FILE_HASHTABLE = "Hashtable128.csv"
```

Pastikan dataset RSSI memiliki kolom `wlan_radio.signal_dbm` agar pipeline dapat berjalan tanpa modifikasi.

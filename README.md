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
| `NIST-Test-Alice.exe` | Executable NIST yang dipakai pipeline untuk validasi bit Alice hasil privacy amplification pada Windows. |
| `NIST-Test-Bob.exe` | Executable NIST untuk validasi bit Bob pada Windows. |
| `sts-2.1.2/` | NIST Statistical Test Suite tambahan sebagai source/referensi validasi keacakan. |

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

5. **Validasi Privacy Amplification dengan NIST**
   - Menguji keacakan bit hasil privacy amplification.
   - Pada Windows, pipeline memakai executable `NIST-Test-Alice.exe` dan `NIST-Test-Bob.exe`.
   - Source NIST STS 2.1.2 juga disertakan pada folder `sts-2.1.2/` sebagai tambahan.
   - Pipeline Python menyiapkan file `Input_NIST_*.csv` sebagai input validasi.

6. **Ekstraksi AES**
   - Mengambil indeks blok yang lolos dari hasil validasi NIST.
   - Menghasilkan kunci AES-128 dalam format heksadesimal.

## Kebutuhan Sistem

- Python 3.10 atau lebih baru
- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `PyWavelets`
- Compiler C seperti `gcc` untuk membangun NIST STS atau wrapper NIST
- Windows executable NIST sudah tersedia:
  - `NIST-Test-Alice.exe`
  - `NIST-Test-Bob.exe`

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
  - Windows: `NIST-Test-Alice.exe` dan `NIST-Test-Bob.exe` sudah disertakan di repository.
  - Linux/Raspberry Pi: build executable dari source/wrapper NIST yang sesuai.

## Validasi Privacy Amplification

Validasi utama pada pipeline Windows menggunakan executable `NIST-Test-Alice.exe` dan `NIST-Test-Bob.exe`. Folder `sts-2.1.2/` disertakan sebagai tambahan source/referensi NIST Statistical Test Suite untuk mengevaluasi keacakan bit setelah tahap privacy amplification.

Pada pipeline ini, tahap privacy amplification menghasilkan file input seperti:

- `Input_NIST_Alice.csv`
- `Input_NIST_Bob.csv`
- `Input_NIST_<prefix>_Alice.csv`
- `Input_NIST_<prefix>_Bob.csv`

File tersebut kemudian divalidasi menggunakan executable NIST yang dipanggil oleh `pipeline_gabungan.py`. Hasil validasi berupa indeks blok yang lolos uji keacakan, misalnya `sudahujinist_Alice_Sken1.csv`, lalu dipakai pada tahap ekstraksi AES untuk memilih blok kunci yang valid.

Untuk membangun NIST STS dari source:

```bash
cd sts-2.1.2
make
```

Perintah tersebut menghasilkan executable `assess`. Pada Windows, build dapat dilakukan melalui lingkungan yang menyediakan `make` dan `gcc`, misalnya MSYS2, MinGW, WSL, atau Linux/Raspberry Pi.

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

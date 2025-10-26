
INFORMATION RETRIEVAL (IR) — PYSerini + Streamlit
=================================================

Ringkasan
---------
Proyek ini adalah sistem *Information Retrieval* (IR) untuk domain berita/analisis finansial di Indonesia.
Pencarian dilakukan menggunakan Lucene (via Pyserini) dengan antarmuka pengguna sederhana berbasis Streamlit.
Anda bisa membuat indeks dari korpus JSONL, lalu menjalankan UI untuk melakukan pencarian leksikal cepat
(BM25 default dari LuceneSearcher).

Fitur Utama
-----------
1) Indexing korpus JSONL (judul, url, contents) ke Lucene.
2) Antarmuka Streamlit yang ringan dan estetis (highlight kata kunci, snippet yang rapi).
3) "ONNX stub" otomatis agar Pyserini tidak mengeluh soal onnxruntime di Windows yang tidak diperlukan untuk pencarian leksikal.
4) Konfigurasi Top-k, panjang snippet, opsi tampilkan skor.
5) Saran penulisan query agar hasil lebih relevan (entitas, angka, waktu).

Struktur Direktori (disarankan)
-------------------------------
.
├─ data/
│  └─ finance_jsonl/
│     └─ corpus.jsonl               # Korpus dalam format JSONL (1 dokumen per baris)
├─ evaluation/                      #
│  └─ ground_truth.json             # Ground truth dari query
│  └─ search_results.json           # Hasil pencarian BM25
├─ indexes/
│  └─ idx_contents/                 # Hasil indeks Lucene (dibuat oleh proses indexing)
├─ user_interface.py                # Aplikasi Streamlit (UI)
├─ indexing.ipynb                   # Notebook contoh proses indexing dan uji coba pencarian
├─ requirements.txt                          # Python requirements
└─ packages.txt                     # Paket sistem (OS-level) yang diperlukan

Persyaratan
-----------
Python packages (requirements.txt):
- streamlit==1.40.2
- pandas
- pyserini==1.2.0

Paket sistem (packages.txt):
- openjdk-21-jdk-headless

Catatan:
- Pyserini/Lucene membutuhkan Java (JDK). Di Linux/WSL bisa pasang paket dari distro.
- Di Windows, bisa pakai winget/choco atau installer JDK resmi. Pastikan `java -version` berfungsi.

Instalasi (Contoh)
------------------
1) Buat dan aktifkan virtual environment (opsional namun disarankan):

   Windows (PowerShell):
   > python -m venv .venv
   > .\.venv\Scripts\Activate.ps1

   Linux/Mac:
   $ python3 -m venv .venv
   $ source .venv/bin/activate

2) Pasang dependensi Python:
   (.venv) $ pip install -r requirements.txt

3) Pasang JDK (bila belum ada):
   - Ubuntu/Debian (root/sudo): 
     # apt-get update && apt-get install -y openjdk-21-jdk-headless
   - Cek versi:
     $ java -version

Menyiapkan Korpus
-----------------
Format korpus adalah JSON Lines (JSONL): satu dokumen per baris.
Setiap baris minimal memiliki kolom berikut:

{
  "id": "doc-0001",
  "title": "Judul Artikel",
  "url": "https://contoh.com/path/artikel",
  "contents": "Isi artikel panjang tanpa pemformatan baris..."
}

Simpan file menjadi:
data/finance_jsonl/corpus.jsonl

Tips:
- `contents` sebaiknya teks bersih (tanpa HTML) dan berbahasa konsisten.
- `title` tidak wajib untuk pencarian, tapi sangat membantu tampilan hasil.
- `id` opsional; Lucene akan memberi docid internal, namun id eksternal berguna untuk tracking.

Membuat Indeks (Indexing)
-------------------------
Anda bisa menjalankan perintah (seperti pada indexing.ipynb) untuk membuat indeks Lucene dari folder JSONL:

$ python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input data/finance_jsonl \
  --index indexes/idx_contents \
  --generator DefaultLuceneDocumentGenerator \
  --threads 2 \
  --storePositions --storeDocvectors --storeRaw

Penjelasan argumen penting:
- --collection JsonCollection : memberitahu Pyserini bahwa korpus berupa JSON/JSONL.
- --input data/finance_jsonl  : folder yang berisi file JSONL Anda.
- --index indexes/idx_contents: lokasi output indeks Lucene.
- --storePositions/Docvectors/Raw: menyimpan info tambahan yang berguna untuk analisis & retrieval.

Uji Pencarian Cepat (Opsional, lewat Notebook)
-----------------------------------------------
Lihat indexing.ipynb untuk contoh kode:
- Memuat LuceneSearcher("indexes/idx_contents")
- Melakukan `search(query, k)`
- Menampilkan judul/url/snippet dari hasil teratas

Menjalankan Antarmuka Streamlit
-------------------------------
1) Pastikan variabel path indeks di user_interface.py sudah benar:
   path_indeks = "indexes/idx_contents"

2) Jalankan aplikasi:
   (.venv) $ streamlit run user_interface.py

3) Buka URL lokal yang tertera (biasanya http://localhost:8501) di browser.

Cara Pakai UI
-------------
- Masukkan query (contoh: "IHSG hari ini", "MIKA Sidoarjo 200 bed", "emiten kelapa sawit target harga")
- Klik "Jalankan Pencarian"
- Atur Top-k hasil, panjang snippet, highlight, dan skor melalui Sidebar
- Setiap kartu hasil berisi: peringkat, domain sumber, judul (klik untuk membuka), snippet, dan tautan

Catatan Teknis (Windows & ONNX)
-------------------------------
- File user_interface.py menyertakan *stub* untuk modul `onnxruntime` agar import Pyserini tidak gagal
  ketika encoder ONNX tidak tersedia (kita hanya memakai pencarian leksikal).
- Jika Anda memiliki `onnxruntime`, tidak masalah—stub hanya dipakai bila import gagal.
- Jika error Java muncul, pastikan `JAVA_HOME` dan `java -version` sudah benar.

Troubleshooting
---------------
1) "Gagal mengimpor Pyserini" → Pastikan:
   - Versi Python kompatibel (3.8-3.12 umumnya aman).
   - JDK terpasang dan `java -version` OK.
   - `pip install -r requirements.txt` sukses tanpa error.

2) "Gagal memuat indeks dari 'indexes/idx_contents'" → Cek:
   - Folder indeks benar-benar ada dan tidak kosong.
   - Hak akses & path relatif/absolut sesuai.
   - Anda menjalankan perintah indexing dengan benar.

3) "Tidak ada hasil" → Coba:
   - Query lebih spesifik (entitas, angka, waktu).
   - Pastikan `contents` korpus berisi teks yang relevan (bukan kosong).

Evaluasi (Opsional, Lanjutan)
-----------------------------
- Anda dapat membuat daftar query + jawaban relevan (qrels) untuk mengevaluasi dengan metrik IR
  (precision@k, recall@k, MAP, nDCG).
- Pyserini menyediakan utilitas untuk evaluasi ketika Anda memiliki qrels dalam format standar TREC.


Evaluasi Otomatis (evaluation.py)
---------------------------------
Script `evaluation.py` menyediakan evaluasi end-to-end terhadap hasil retrieval BM25/Lucene menggunakan metrik standar IR.

**Metrik yang dihitung**
- **Precision@k (P@k)**: proporsi dokumen relevan di antara k hasil teratas.
- **Recall@k (R@k)**: proporsi dokumen relevan yang berhasil diambil di k hasil teratas.
- **MAP** (Mean Average Precision): rerata AP di seluruh query (AP menghitung presisi setiap kali menemukan dokumen relevan).
- **nDCG@k**: normalisasi *Discounted Cumulative Gain* hingga k (memperhitungkan urutan dan *gain* relasi > 1 bila ada).

**Format input**
- `queries.tsv`: `qid<TAB>query`
  ```tsv
  Q1	IHSG hari ini
  Q2	ekspansi RS MIKA Sidoarjo 200 bed theranostic
  Q3	proyeksi target harga emiten kelapa sawit Indonesia
  ```
- `qrels.tsv`: `qid<TAB>docid<TAB>rel`
  ```tsv
  Q1	doc-000123	1
  Q1	doc-000987	0
  Q2	doc-000555	2    # nilai > 1 akan dipakai sebagai gain untuk nDCG
  ```
  *Catatan:* Format TREC (`qid 0 docid rel`) juga didukung.

**Menjalankan evaluasi**
```bash
# Ambil indeks yang sudah dibuat sebelumnya pada indexes/idx_contents
python evaluation.py \
  --index indexes/idx_contents \
  --queries data/queries.tsv \
  --qrels data/qrels.tsv \
  --k 10 \
  --out runs/run_k10
```

**Output**
- `runs/run_k10.jsonl` — hasil per-query berisi: retrieved@k, precision@k, recall@k, AP, nDCG@k, dst.
- `runs/run_k10.summary.json` — ringkasan macro: P@k, R@k, MAP, nDCG@k, jumlah query, nilai k.

**Tips & Troubleshooting evaluasi**
- Pastikan `docid` pada `qrels.tsv` sesuai dengan `docid` di indeks Lucene (bukan `id` di payload json, kecuali memang itu yang dipakai saat indexing).
- Jika semua `rel = 0`, maka MAP dan nDCG akan 0—pastikan ada minimal satu dokumen relevan per query.
- Untuk analisis lebih dalam, naikkan kedalaman retrieval (script sudah mengambil hingga `max(k,100)` agar AP/nDCG lebih stabil).

**Contoh alur cepat**
```bash
# 1) Siapkan queries.tsv dan qrels.tsv
mkdir -p data runs

# 2) Jalankan evaluasi
python evaluation.py --index indexes/idx_contents \
  --queries data/queries.tsv --qrels data/qrels.tsv \
  --k 10 --out runs/finance_k10

# 3) Lihat ringkasan
type runs/finance_k10.summary.json   # Windows (PowerShell: Get-Content)
cat runs/finance_k10.summary.json    # Linux/Mac
```

Lisensi & Kredit
----------------
- Pyserini: https://github.com/castorini/pyserini (Lisensi Apache-2.0)
- Streamlit: https://streamlit.io/
- Lucene: https://lucene.apache.org/

Catatan Tambahan
----------------
- Proyek ini fokus pada pencarian leksikal. Integrasi ke dense-retrieval/bi-encoder dapat dieksplorasi
  di masa depan (membutuhkan dependensi tambahan seperti onnx/FAISS, dsb.).
- Jika ingin mengubah desain UI, edit CSS di blok st.markdown(…style…).
- Pastikan data yang digunakan mematuhi kebijakan privasi dan hak cipta.

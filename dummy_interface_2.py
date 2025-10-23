# --- imports standar (tanpa st.* dulu) ---
import os, shutil, pathlib, subprocess
import json, time, re, sys, types
from typing import Any, List, Dict
import streamlit as st

# WAJIB: ini harus jadi perintah Streamlit pertama
st.set_page_config(page_title="IR UI • Pyserini", page_icon="🔎", layout="wide")

# (baru setelah itu) judul, CSS, dsb.
st.title("🔎 Information Retrieval System untuk Domain Berita Finance")

def _ensure_java_home():
    javac = shutil.which("javac")
    if not javac:
        st.error("JDK tidak ditemukan. Pastikan packages.txt berisi 'openjdk-17-jdk-headless'.")
        st.stop()

    real = pathlib.Path(javac).resolve()                 # /usr/bin/javac -> .../jvm/java-17-openjdk-amd64/bin/javac
    java_home = real.parent.parent                       # .../jvm/java-17-openjdk-amd64
    libserver = java_home / "lib" / "server"             # .../lib/server
    libjvm = libserver / "libjvm.so"                     # .../lib/server/libjvm.so

    if not libjvm.exists():
        st.error(f"libjvm.so tidak ditemukan di: {libjvm}\n"
                 "Pastikan paket JDK (bukan JRE) terpasang: openjdk-17-jdk-headless.")
        st.stop()

    # Set env untuk loader
    os.environ["JAVA_HOME"] = str(java_home)
    os.environ["JAVAHOME"]  = str(java_home)
    os.environ["PATH"] = f"{java_home}/bin:{libserver}:{os.environ.get('PATH','')}"
    # LD_LIBRARY_PATH perlu di-set sebelum pyjnius load JVM
    os.environ["LD_LIBRARY_PATH"] = f"{libserver}:{os.environ.get('LD_LIBRARY_PATH','')}"

    # Hint eksplisit ke pyjnius: gunakan libjvm.so ini
    try:
        import jnius_config
        jnius_config.set_jvm_path(str(libjvm))
    except Exception:
        # kalau pyjnius belum terinstall di saat ini, abaikan; Pyserini akan import belakangan
        pass

    return str(java_home)

JAVA_HOME_SET = _ensure_java_home()
# opsional: tampilkan versi Java
try:
    out = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT).decode()
    st.caption(f"Java OK · JAVA_HOME={JAVA_HOME_SET}")
except Exception:
    pass


JAVA_HOME_SET = _ensure_java_home()


import sys, types
def _pasang_stub_onnx():
    """Memasang modul palsu 'onnxruntime' agar Pyserini tidak error saat import encoder."""
    stub = types.ModuleType("onnxruntime")
    class _Dummy:
        def __init__(self, *a, **k): pass
    stub.SessionOptions = _Dummy
    stub.InferenceSession = _Dummy
    stub.get_available_providers = lambda: []
    sys.modules["onnxruntime"] = stub

try:
    import onnxruntime  # noqa
except Exception:
    _pasang_stub_onnx()
# --- Selesai patch stub ---

path_indeks = "indexes/idx_contents"


st.markdown(
    """
    <style>
    .result-card{border:1px solid #2a2f3a;border-radius:16px;padding:18px;margin:14px 0;
                 background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.00));
                 box-shadow:0 8px 24px rgba(0,0,0,0.15)}
    .result-title{font-weight:700;font-size:1.08rem;margin:0 0 6px 0;line-height:1.35}
    .result-title a{color:inherit;text-decoration:none}
    .result-title a:hover{text-decoration:underline}
    .result-snippet{color:#c9d1d9;line-height:1.6;font-size:0.95rem;margin:4px 0 10px}
    .result-link a{font-weight:600;text-decoration:none}
    .chip{display:inline-block;padding:3px 10px;border-radius:999px;background:#0ea5e933;
          color:#7dd3fc;font-size:0.78rem;margin-right:8px;border:1px solid #0ea5e9}
    .meta{color:#9ba1a6;font-size:0.8rem;margin-bottom:8px}
    .highlight{background:#fde04733;padding:0 2px;border-radius:4px}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utilitas & Cache
# -----------------------------
@st.cache_resource(show_spinner=False)
def muat_searcher(path_indeks: str) -> Any:
    """Membuat/caching LuceneSearcher dari path indeks (lazy import)."""
    try:
        from pyserini.search.lucene import LuceneSearcher
    except Exception as e:
        st.error(
            "Gagal mengimpor Pyserini (kemungkinan terkait Java/JDK atau onnxruntime).\n\n"
            f"{type(e).__name__}: {e}"
        )
        st.stop()
    return LuceneSearcher(path_indeks)


def lakukan_pencarian(searcher: Any, query: str, k: int) -> List[Dict]:
    hits = searcher.search(query, k=k)
    hasil = []
    for i, h in enumerate(hits, 1):
        # docid & score bisa atribut; antisipasi jika callable
        docid_attr = getattr(h, "docid", None)
        docid = docid_attr() if callable(docid_attr) else docid_attr
        score_attr = getattr(h, "score", 0.0)
        score = float(score_attr() if callable(score_attr) else score_attr)

        judul = url = snippet = ""
        try:
            doc = searcher.doc(docid)
            raw = doc.raw() if doc is not None else None
        except Exception:
            raw = None

        if raw:
            try:
                obj = json.loads(raw)
                judul = (obj.get("title", "") or "").strip()
                url = obj.get("url", "") or ""
                konten = obj.get("contents", "") or ""
                snippet = konten.replace("\n", " ")
            except Exception:
                pass

        hasil.append({
            "rank": i, "docid": docid, "score": score,
            "title": judul, "url": url, "snippet": snippet
        })
    return hasil


# -----------------------------
# Sidebar Pengaturan
# -----------------------------
with st.sidebar:
    st.header("⚙️ Pengaturan")
    top_k = st.slider("Top-k hasil", 1, 50, 10, help="Banyaknya hasil ditampilkan")
    snippet_words = st.slider("Panjang snippet (kata)", 15, 120, 40)
    highlight_on = st.toggle("Highlight kata query", value=True)
    show_scores = st.toggle("Tampilkan skor dokumen", value=False)
    st.markdown("---")
    st.subheader("💡 Tips")
    st.markdown(
        """
        **Tips menulis query**  
        • Spesifikkan entitas/angka/waktu (mis. *IHSG hari ini*, *MIKA Sidoarjo 200 bed*).  
        • Gunakan kata kunci unik untuk mempersempit hasil.  
        • Tambahkan konteks jika perlu (sektor, emiten, lokasi).
        """
    )



# -----------------------------
# Input Query (tunggal)
# -----------------------------
query_tunggal = st.text_input("Masukkan query", value="")
jalankan = st.button("🚀 Jalankan Pencarian")

# -----------------------------
# Eksekusi & Tampilan Hasil
# -----------------------------
if jalankan:
    if not path_indeks:
        st.error("Path indeks tidak boleh kosong.")
        st.stop()

    try:
        with st.spinner("Memuat indeks…"):
            searcher = muat_searcher(path_indeks)
    except Exception as e:
        st.error(f"Gagal memuat indeks dari '{path_indeks}'.\nDetail: {e}")
        st.stop()

    q = (query_tunggal or "").strip()
    if not q:
        st.warning("Masukkan query terlebih dahulu.")
        st.stop()
    
    # helper: highlight + potong snippet rapi
    def _tokens(s: str):
        return re.findall(r"[A-Za-z0-9]+", s.lower())

    query_terms = {t for t in _tokens(q) if len(t) >= 3}

    def potong_kalimat(teks: str, max_words: int) -> str:
        words = teks.split()
        return " ".join(words) if len(words) <= max_words else " ".join(words[:max_words]) + " …"

    def highlight_terms(teks: str) -> str:
        def repl(m):
            w = m.group(0)
            return f"<span class='highlight'>{w}</span>" if w.lower() in query_terms else w
        return re.sub(r"\b[\w-]+\b", repl, teks)

    # style kecil untuk highlight (dipasang sekali)
    st.markdown(
        "<style>.highlight{background:#fde04733;padding:0 2px;border-radius:4px}</style>",
        unsafe_allow_html=True,
    )

    t0 = time.time()
    hasil = lakukan_pencarian(searcher, q, k=top_k)
    dt = (time.time() - t0) * 1000
    st.success(f"Selesai dalam {dt:.0f} ms. Menampilkan {len(hasil)} hasil.")

    if not hasil:
        st.info("Tidak ada hasil.")
    else:
        st.markdown(f"### 🔍 Query: `{q}`")
        for r in hasil:
            judul = r["title"] or r["docid"]
            snippet_raw = r["snippet"] or "(tidak ada cuplikan)"
            snippet = potong_kalimat(snippet_raw, snippet_words)
            if highlight_on:
                snippet = highlight_terms(snippet)

            url = r["url"]

            # domain kecil di meta
            domain = ""
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace("www.", "")
                except Exception:
                    domain = ""

            # === meta: rank · domain · skor (opsional) ===
            meta_parts = [f"<span class='chip'>#{r['rank']}</span>"]
            if domain:
                meta_parts.append(domain)
            if show_scores:
                meta_parts.append(f"skor {r['score']:.4f}")
            meta_html = " · ".join(meta_parts)

            st.markdown(
                f"""
                <div class='result-card'>
                    <div class='meta'>{meta_html}</div>
                    <div class='result-title'>{f"<a href='{url}' target='_blank'>{judul}</a>" if url else judul}</div>
                    <div class='result-snippet'>{snippet}</div>
                    {f"<div class='result-link'>↗️ <a href='{url}' target='_blank'>Buka tautan</a></div>" if url else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )



            

# -----------------------------
# Footer (Tentang Aplikasi)
# -----------------------------
st.markdown("---")
st.subheader("ℹ️ Tentang Aplikasi")
st.markdown(
    """
    Sistem ini adalah aplikasi *information retrieval* berbasis **Lucene** (via **Pyserini**) yang
    membantu menemukan artikel relevan dari korpus finansial/ekonomi secara cepat.
    Masukkan sebuah query; sistem menampilkan **judul**, **cuplikan isi**, dan **tautan** ke sumber aslinya.

    **Cara kerja singkat**  
    • Dokumen diproses dan diindeks ke Lucene.  
    • Saat menerima query, sistem melakukan pencarian leksikal & menghitung skor relevansi.  
    • Hasil ditampilkan sebagai kartu dengan snippet yang dipotong agar ringkas (dilengkapi highlight kata kunci jika diaktifkan).

    **Saran penggunaan**  
    • Tulis query spesifik (entitas/angka/waktu) agar hasil lebih relevan, mis. *“IHSG hari ini”*, *“MIKA Sidoarjo 200 bed”*.
    """
)
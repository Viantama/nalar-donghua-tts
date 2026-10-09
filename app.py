import asyncio
import re
import tempfile
from pathlib import Path

import edge_tts
import streamlit as st

st.set_page_config(
    page_title="NALAR DONGHUA — AI Voiceover Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Dark, responsive styling
st.markdown(
    """
    <style>
      .stApp { background: #0b0d12; color: #eef2ff; }
      .block-container { max-width: 1050px; padding-top: 2rem; padding-bottom: 3rem; }
      h1, h2, h3 { color: #f5f7ff; }
      .hero {
        padding: 1.5rem 1.6rem; border: 1px solid #292e3b; border-radius: 20px;
        background: linear-gradient(135deg, #171b27 0%, #10131c 65%, #1c1426 100%);
        margin-bottom: 1.25rem;
      }
      .eyebrow { color: #b8a2ff; font-size: .78rem; letter-spacing: .18em; font-weight: 700; }
      .subtle { color: #a7afc2; }
      div[data-testid="stTextArea"] textarea {
        background: #111520; color: #f3f5fb; border: 1px solid #30384a; border-radius: 12px;
      }
      div[data-testid="stSelectbox"] > div > div,
      div[data-testid="stNumberInput"] input { background: #111520; }
      .stButton > button {
        width: 100%; border: 0; border-radius: 12px; padding: .75rem 1rem;
        color: white; font-weight: 700;
        background: linear-gradient(90deg, #7557e8, #9b59d7);
      }
      .stDownloadButton > button {
        width: 100%; border-radius: 12px; font-weight: 700;
        border: 1px solid #6e59ce; background: #19172a; color: #eee9ff;
      }
      hr { border-color: #292e3b; }
      .hint { padding: .85rem 1rem; background: #111520; border: 1px solid #292e3b;
              border-radius: 12px; color: #b8c0d2; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">NALAR DONGHUA</div>
      <h1 style="margin:.35rem 0 .3rem 0;">AI Voiceover Studio</h1>
      <div class="subtle">Ubah naskah rekap donghua menjadi narasi audio yang siap diedit.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

def normalize_pronunciation(text: str):
    """Apply whole-word replacements without changing parts of unrelated words."""
    replacements = [
        (r"(?i)\bXiao\b", "Siao"),
        (r"(?i)\bQing\b", "Ching"),
        (r"(?i)\bChen\b", "Cen"),
        (r"(?i)\bSect\b", "Sekte"),
    ]
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)
    return result

def make_ssml_voice(text: str, voice: str, rate: int, pitch: int) -> str:
    # edge-tts accepts rate and pitch directly; this helper documents the intended values.
    return text

async def synthesize(text: str, voice: str, rate: int, pitch: int, output_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=f"{rate:+d}%",
        pitch=f"{pitch:+d}Hz",
    )
    await communicate.save(output_path)

with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    voice_label = st.selectbox(
        "Suara narator",
        ["Ardi — Pria", "Gadis — Wanita"],
        help="Pilihan suara neural Bahasa Indonesia.",
    )
    voice = "id-ID-ArdiNeural" if voice_label.startswith("Ardi") else "id-ID-GadisNeural"
    rate = st.slider("Kecepatan bicara", min_value=-30, max_value=30, value=0, step=5, format="%d%%")
    pitch = st.slider("Nada suara", min_value=-20, max_value=20, value=0, step=5, format="%dHz")
    auto_fix = st.toggle("Benahi ejaan otomatis", value=True)
    st.markdown("---")
    st.caption("Memerlukan koneksi internet saat membuat audio. Tidak membutuhkan API key, tetapi layanan suara Microsoft tetap dipanggil secara online.")

left, right = st.columns([1.65, 1], gap="large")
with left:
    st.markdown("### 📝 Naskah narasi")
    raw_text = st.text_area(
        "Masukkan naskah",
        height=330,
        placeholder="Tempel naskah rekap donghua kamu di sini...\n\nContoh: Xiao Yan akhirnya bertemu Chen...",
        label_visibility="collapsed",
        max_chars=50000,
    )
    processed_text = normalize_pronunciation(raw_text) if auto_fix else raw_text
    if raw_text.strip():
        with st.expander("Pratinjau teks yang akan dibacakan"):
            st.write(processed_text)
            if processed_text != raw_text:
                st.caption("Ejaan yang cocok dengan kamus otomatis telah disesuaikan.")
    st.caption(f"{len(raw_text):,} karakter")

with right:
    st.markdown("### 🎚️ Setelan aktif")
    st.markdown(
        f"""
        <div class="hint">
          <b>Suara:</b> {voice_label}<br>
          <b>Kecepatan:</b> {rate:+d}%<br>
          <b>Nada:</b> {pitch:+d} Hz<br>
          <b>Kamus ejaan:</b> {"Aktif" if auto_fix else "Nonaktif"}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown("**Tips narasi**")
    st.write("• Mulai dari kecepatan 0% untuk hasil natural.")
    st.write("• Pecah naskah sangat panjang menjadi beberapa bagian.")
    st.write("• Dengarkan hasilnya sebelum dipakai di video.")

generate = st.button("🎙️ Generate Voice", type="primary")

if generate:
    if not raw_text.strip():
        st.warning("Masukkan naskah terlebih dahulu.")
    else:
        with st.spinner("Sedang membuat audio... Jangan tutup halaman ini."):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            output_path = temp_file.name
            temp_file.close()
            try:
                asyncio.run(synthesize(processed_text, voice, rate, pitch, output_path))
                st.session_state["tts_audio_path"] = output_path
                st.session_state["tts_audio_text"] = processed_text
                st.session_state["tts_audio_voice"] = voice_label
            except Exception as exc:
                Path(output_path).unlink(missing_ok=True)
                st.error(
                    "Audio gagal dibuat. Periksa koneksi internet, lalu coba lagi. "
                    "Jika masalah berlanjut, layanan TTS mungkin sedang tidak tersedia."
                )
                st.caption(f"Detail teknis: {exc}")

audio_path = st.session_state.get("tts_audio_path")
if audio_path and Path(audio_path).exists():
    st.markdown("---")
    st.markdown("### 🔊 Hasil audio")
    st.audio(Path(audio_path).read_bytes(), format="audio/mp3")
    st.download_button(
        "⬇️ Unduh MP3",
        data=Path(audio_path).read_bytes(),
        file_name="nalar_donghua_voiceover.mp3",
        mime="audio/mpeg",
    )
    st.caption(f"Suara: {st.session_state.get('tts_audio_voice', '—')} • File sementara pada server aplikasi.")

st.markdown("---")
st.markdown(
    '<div class="subtle" style="text-align:center;font-size:.85rem;">NALAR DONGHUA • AI Voiceover Studio</div>',
    unsafe_allow_html=True,
)

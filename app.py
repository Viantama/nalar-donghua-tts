import asyncio
import re
import tempfile
from pathlib import Path

import edge_tts
import streamlit as st

st.set_page_config(page_title="NALAR DONGHUA — AI Voiceover Studio", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
.stApp { background: #0b0d12; color: #eef2ff; }
.block-container { max-width: 850px; padding-top: 1.2rem; padding-bottom: 2.5rem; }
h1, h2, h3 { color: #f5f7ff; }
div[data-testid="stTextArea"] textarea { background: #111520; color: #f3f5fb; }
div[data-testid="stSelectbox"] > div > div { background: #111520; }
.stButton > button, .stDownloadButton > button { width: 100%; border-radius: 12px; font-weight: 700; padding: .7rem 1rem; }
.hero { padding: 1.2rem; border: 1px solid #292e3b; border-radius: 18px; background: linear-gradient(135deg, #171b27 0%, #10131c 100%); margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div style="color:#b8a2ff;letter-spacing:.16em;font-weight:700;font-size:.8rem">NALAR DONGHUA</div>
  <h1 style="margin:.35rem 0">🎙️ AI Voiceover Studio</h1>
  <div style="color:#a7afc2">Ubah naskah rekap donghua menjadi narasi audio MP3.</div>
</div>
""", unsafe_allow_html=True)

def normalize_pronunciation(text: str) -> str:
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

async def synthesize(text: str, voice: str, rate: int, pitch: int, output_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz")
    await communicate.save(output_path)

st.subheader("⚙️ Pengaturan suara")
voice_label = st.selectbox("Suara narator", ["Ardi — Pria", "Gadis — Wanita"])
voice = "id-ID-ArdiNeural" if voice_label.startswith("Ardi") else "id-ID-GadisNeural"
rate = st.slider("Kecepatan bicara", min_value=-10, max_value=10, value=0, step=5, help="Mulai dari 0% untuk kecepatan normal.")
pitch = st.slider("Nada suara", min_value=-5, max_value=5, value=0, step=5, help="0 Hz adalah nada standar.")
auto_fix = st.toggle("Benahi ejaan otomatis", value=True)
st.caption("Membutuhkan koneksi internet saat membuat audio.")

st.divider()
st.subheader("📝 Naskah narasi")
raw_text = st.text_area("Masukkan naskah", height=280, placeholder="Tempel naskah rekap donghua kamu di sini...\n\nContoh: Xiao Yan bertemu Chen...", label_visibility="collapsed", max_chars=50000)
processed_text = normalize_pronunciation(raw_text) if auto_fix else raw_text

if raw_text.strip() and auto_fix and processed_text != raw_text:
    with st.expander("Pratinjau teks yang akan dibacakan"):
        st.write(processed_text)
        st.caption("Ejaan yang cocok dengan kamus otomatis telah disesuaikan.")

st.caption(f"{len(raw_text):,} karakter")
st.markdown("**Tips narasi**")
st.write("• Mulai dari kecepatan 0% untuk hasil natural.")
st.write("• Pecah naskah sangat panjang menjadi beberapa bagian.")
st.write("• Dengarkan hasilnya sebelum dipakai di video.")

if st.button("🎙️ Generate Voice", type="primary", use_container_width=True):
    if not raw_text.strip():
        st.warning("Masukkan naskah terlebih dahulu.")
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = temp_file.name
        temp_file.close()
        try:
            with st.spinner("Sedang membuat audio... Jangan tutup halaman ini."):
                asyncio.run(synthesize(processed_text, voice, rate, pitch, output_path))
            st.session_state["tts_audio_path"] = output_path
            st.session_state["tts_audio_voice"] = voice_label
            st.session_state["tts_audio_rate"] = rate
            st.session_state["tts_audio_pitch"] = pitch
        except Exception as exc:
            Path(output_path).unlink(missing_ok=True)
            st.error("Audio gagal dibuat. Periksa koneksi internet lalu coba lagi.")
            st.caption(f"Detail teknis: {exc}")

audio_path = st.session_state.get("tts_audio_path")
if audio_path and Path(audio_path).exists():
    st.divider()
    st.subheader("🎧 Hasil audio")
    st.caption(f"Suara: {st.session_state.get('tts_audio_voice', '-')} · Kecepatan: {st.session_state.get('tts_audio_rate', 0):+d}% · Nada: {st.session_state.get('tts_audio_pitch', 0):+d} Hz")
    audio_bytes = Path(audio_path).read_bytes()
    st.audio(audio_bytes, format="audio/mp3")
    st.download_button("⬇️ Unduh MP3", data=audio_bytes, file_name="nalar_donghua_voiceover.mp3", mime="audio/mpeg", use_container_width=True)

st.divider()
st.caption("NALAR DONGHUA · AI Voiceover Studio")

import streamlit as st # type: ignore
from tensorflow.keras.models import load_model # type: ignore
from PIL import Image # type: ignore
import numpy as np # type: ignore
import datetime
import requests # type: ignore
import matplotlib.pyplot as plt # type: ignore
from io import BytesIO
import time
import pandas as pd # type: ignore
import os

# === Load model AI ===
model = load_model("model_sampah_metal_vs_non_metal_final.h5")

# === Inisialisasi session state ===
if "history" not in st.session_state:
    st.session_state.history = []
if "streaming" not in st.session_state:
    st.session_state.streaming = False

# === Konfigurasi halaman ===
st.set_page_config(page_title="Klasifikasi Sampah", layout="wide")

# === Fungsi prediksi ===
def predict_image(img, threshold=0.5):
    img = img.convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array)[0][0]
    label = "Non Metal" if prediction > threshold else "Metal"
    confidence = prediction if prediction > threshold else 1 - prediction
    return label, confidence, prediction

# === Fungsi kirim ke ESP32 ===
def send_prediction_to_esp32(label, confidence):
    url = "http://localhost:5000/prediksi"
    payload = {
        "label": label,
        "confidence": f"{confidence*100:.2f}%"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.toast("✅ Prediksi dikirim ke ESP32", icon="📡")
        else:
            st.warning("⚠️ Gagal kirim ke ESP32.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# === Styling Header ===
st.markdown("""
    <style>
    .main {background-color: #f0f2f6;}
    h1 {text-align: center; color: #1f77b4;}
    </style>
""", unsafe_allow_html=True)

st.title("♻️ Sistem Klasifikasi Sampah Metal & Non-Metal")

# === Sidebar Navigasi ===
st.sidebar.title("Menu")
menu = st.sidebar.radio("Pilih Halaman:", [
    "🏠 Beranda", "🔍 Deteksi Sampah", "🕒 Riwayat Deteksi Sampah", "📡 Monitoring Sampah", "🎁 Konversi Poin"
])

# === Halaman: Beranda ===
if menu == "🏠 Beranda":
    st.header("🌟 Profil Kelompok - Samsung Innovation Campus")
    st.write("""
        Kami adalah tim yang tergabung dalam program Samsung Innovation Campus. 
        Proyek kami berfokus pada sistem klasifikasi sampah berbasis **AI** yang terhubung dengan **ESP32-CAM** dan **dashboard Ubidots** untuk pengelolaan data.
        
        Sistem ini mampu mengklasifikasikan sampah menjadi **Metal** dan **Non-Metal** secara otomatis dan mengirimkan hasil klasifikasi ke ESP32 serta menyimpan riwayat prediksi.
    """)
    
    st.markdown("### 👥 Anggota Kelompok:")
    cols = st.columns(4)
    anggota_images = [
        ("img_anggota/anggota1.jpg", "Nama 1"),
        ("img_anggota/anggota2.jpg", "Nama 2"),
        ("img_anggota/anggota3.jpg", "Nama 3"),
        ("img_anggota/anggota4.jpg", "Nama 4"),
    ]

    for col, (path, caption) in zip(cols, anggota_images):
        with col:
            if os.path.exists(path):
                st.image(path, caption=caption, use_container_width=True)
            else:
                st.warning(f"Gambar '{caption}' tidak ditemukan.")

# === Halaman: Deteksi Langsung ===
elif menu == "🔍 Deteksi Sampah":
    st.subheader("Live Stream dari ESP32-CAM")
    col1, col2 = st.columns([1, 1])

    with col1:
        if not st.session_state.streaming and st.button("▶️ Mulai Stream"):
            st.session_state.streaming = True
    with col2:
        if st.session_state.streaming and st.button("⏹️ Stop Stream"):
            st.session_state.streaming = False

    image_placeholder = st.empty()
    info_placeholder = st.empty()
    error_placeholder = st.empty()

    if st.session_state.streaming:
        url = "http://192.168.1.53:5000/get_image"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                error_placeholder.empty()
                img = Image.open(BytesIO(response.content))
                image_placeholder.image(img, caption="📸 Gambar dari ESP32", use_container_width=True)

                label, confidence, _ = predict_image(img)
                info_placeholder.success(f"🎯 Prediksi: **{label}** | 📊 Confidence: **{confidence*100:.2f}%**")

                st.caption("Kategori:")
                if label == "Metal":
                    st.info("🔩 Metal: Kaleng, besi, aluminium")
                else:
                    st.info("🧴 Non-Metal: Plastik, kertas, kain")

                st.session_state.history.append({
                    "label": label,
                    "confidence": f"{confidence*100:.2f}%",
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                })

                send_prediction_to_esp32(label, confidence)
            else:
                error_placeholder.warning("🚫 Gagal mengambil gambar dari ESP32.")
        except Exception as e:
            error_placeholder.error(f"🚫 Error: {e}")
        time.sleep(5)

# === Halaman: Riwayat ===
elif menu == "🕒 Riwayat Deteksi Sampah":
    st.subheader("🕒 Riwayat Prediksi")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada prediksi dilakukan.")

# === Halaman: Tampilan Ubidots ===
elif menu == "📡 Monitoring Sampah ":
    st.subheader("📡 Visualisasi dari Ubidots")
    st.markdown("Berikut adalah tampilan visualisasi data dari Ubidots:")
    col1, col2 = st.columns(2)
    with col1:
        st.components.v1.iframe(
            src="https://stem.ubidots.com/app/dashboards/public/widget/FU4N9kEouMc5kEGVzQg1Ol7Z5qDOgZFgeb3BKQshcC0",
            width=300, height=300
        )
    with col2:
        st.components.v1.iframe(
            src="https://stem.ubidots.com/app/dashboards/public/widget/qBFXyPNOgF5CtWAovTa6IMLS8s6J4OKMygas44HeAGw",
            width=300, height=300
        )

# === Halaman: Konversi Poin ===
elif menu == "🎁 Konversi Poin":
    st.subheader("🎁 Konversi Berat Sampah ke Poin")
    st.markdown("Masukkan berat sampah (dalam gram) untuk dikonversi menjadi poin. Setiap 1 gram = 1 poin.")

    berat = st.number_input("🔢 Masukkan berat sampah (gram):", min_value=0.0, format="%.2f", step=1.0)
    if st.button("🔄 Konversi"):
        poin = int(berat)
        waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"🎉 Anda mendapatkan **{poin} poin** dari {berat:.2f} gram sampah!")

        if "konversi_history" not in st.session_state:
            st.session_state.konversi_history = []
        st.session_state.konversi_history.append({
            "berat (gram)": f"{berat:.2f}",
            "poin": poin,
            "waktu": waktu
        })

    if "konversi_history" in st.session_state and st.session_state.konversi_history:
        st.markdown("#### 📄 Riwayat Konversi")
        df_konversi = pd.DataFrame(st.session_state.konversi_history)
        st.dataframe(df_konversi, use_container_width=True)

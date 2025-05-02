import streamlit as st
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import datetime
import requests
import matplotlib.pyplot as plt
from io import BytesIO
import time

# Memuat model
model = load_model("model_sampah_metal_vs_non_metal_final.h5")

# Inisialisasi state
if "history" not in st.session_state:
    st.session_state.history = []
if "streaming" not in st.session_state:
    st.session_state.streaming = False

# Fungsi prediksi
def predict_image(img, threshold=0.5):
    img = img.convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array)[0][0]
    label = "Non Metal" if prediction > threshold else "Metal"
    confidence = prediction if prediction > threshold else 1 - prediction
    return label, confidence, prediction

# Fungsi kirim prediksi
def send_prediction_to_esp32(label, confidence):
    url = "http://localhost:5000/prediksi"
    payload = {
        "label": label,
        "confidence": f"{confidence*100:.2f}%"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success("✅ Prediksi dikirim ke ESP32", icon="📡")
        else:
            st.warning("⚠️ Gagal kirim ke ESP32.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# UI
st.set_page_config(page_title="Klasifikasi Sampah", page_icon="♻️", layout="centered")
st.markdown("<h1 style='text-align: center; color: green;'>♻️ Klasifikasi Sampah</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Deteksi apakah sampah merupakan <b>Metal</b> atau <b>Non Metal</b>.</p>", unsafe_allow_html=True)
st.markdown("---")

st.subheader("Gambar dari ESP32-CAM")
image_placeholder = st.empty()
info_placeholder = st.empty()
error_placeholder = st.empty()

# Tombol kontrol streaming
col1, col2 = st.columns([1, 1])
with col1:
    if not st.session_state.streaming:
        if st.button("▶️ Mulai Stream"):
            st.session_state.streaming = True
with col2:
    if st.session_state.streaming:
        if st.button("⏹️ Stop Stream"):
            st.session_state.streaming = False

# Stream loop
if st.session_state.streaming:
    url = "http://192.168.1.42:5000/get_image"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            error_placeholder.empty()
            img = Image.open(BytesIO(response.content))
            image_placeholder.image(img, caption="📸 Gambar dari ESP32", use_container_width=True)

            # Prediksi
            label, confidence, raw_pred = predict_image(img)
            info_placeholder.success(f"🎯 Prediksi: {label} | 📊 Confidence: {confidence*100:.2f}%")

            if label == "Metal":
                st.info("🔩 Kategori Metal: kaleng, besi, aluminium, dll.")
            else:
                st.info("🧴 Kategori Non Metal: plastik, kertas, kain, dll.")

            # Tambah ke riwayat
            st.session_state.history.append({
                "filename": "ESP32",
                "label": label,
                "confidence": f"{confidence*100:.2f}%",
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            })

            # Kirim ke ESP32
            send_prediction_to_esp32(label, confidence)

        else:
            error_placeholder.warning("🚫 Gagal mengambil gambar dari ESP32.")

    except Exception as e:
        error_placeholder.error(f"🚫 Gagal mengambil gambar: {e}")

    time.sleep(5)

# Riwayat prediksi
st.markdown("---")
if st.session_state.history:
    st.subheader("🕒 Riwayat Prediksi")
    with st.expander("Lihat Riwayat"):
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            st.write(f"**{i}.** `{item['filename']}` - {item['label']} ({item['confidence']}) 🕔 {item['timestamp']}")

# Grafik pie
def show_summary_chart():
    metal = sum(1 for item in st.session_state.history if item['label'] == "Metal")
    non_metal = sum(1 for item in st.session_state.history if item['label'] == "Non Metal")
    if metal + non_metal == 0:
        return

    labels = ['Metal', 'Non Metal']
    sizes = [metal, non_metal]
    colors = ['#FF9999', '#66B2FF']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
           colors=colors, wedgeprops={'width': 0.4})
    ax.axis('equal')
    st.subheader("📊 Distribusi Kategori Sampah")
    st.pyplot(fig)
show_summary_chart()

# Grafik Bar: Jumlah klasifikasi per kategori
def show_bar_chart():
    metal = sum(1 for item in st.session_state.history if item['label'] == "Metal")
    non_metal = sum(1 for item in st.session_state.history if item['label'] == "Non Metal")

    if metal + non_metal == 0:
        return

    st.subheader("📊 Jumlah Prediksi per Kategori")
    fig, ax = plt.subplots()
    ax.bar(['Metal', 'Non Metal'], [metal, non_metal], color=['#FF9999', '#66B2FF'])
    ax.set_ylabel("Jumlah")
    st.pyplot(fig)

show_bar_chart()

# Grafik Line: Confidence dari waktu ke waktu
def show_line_chart():
    if not st.session_state.history:
        return

    timestamps = [item['timestamp'] for item in st.session_state.history]
    confidences = [float(item['confidence'].replace('%', '')) for item in st.session_state.history]
    labels = [item['label'] for item in st.session_state.history]

    st.subheader("📈 Confidence dari Waktu ke Waktu")
    fig, ax = plt.subplots()
    ax.plot(timestamps, confidences, marker='o', color='green')
    ax.set_xlabel("Waktu")
    ax.set_ylabel("Confidence (%)")
    ax.set_xticks(timestamps)
    ax.set_xticklabels(timestamps, rotation=45, ha='right')
    ax.grid(True)
    st.pyplot(fig)

show_line_chart()

# Unduh CSV
def download_history_as_csv():
    if not st.session_state.history:
        return

    import pandas as pd
    df = pd.DataFrame(st.session_state.history)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Riwayat sebagai CSV",
        data=csv,
        file_name="riwayat_klasifikasi_sampah.csv",
        mime="text/csv"
    )

    
download_history_as_csv()

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

# Inisialisasi session_state
if "history" not in st.session_state:
    st.session_state.history = []

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

# Kirim prediksi ke ESP32
def send_prediction_to_esp32(label, confidence):
    url = "http://localhost:5000/prediksi"
    payload = {
        "label": label,
        "confidence": f"{confidence*100:.2f}%"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success("Prediksi berhasil dikirim ke ESP32!")
        else:
            st.warning("Gagal mengirim prediksi ke ESP32.")
    except Exception as e:
        st.error(f"Error: {e}")

# Pengaturan halaman
st.set_page_config(page_title="Klasifikasi Sampah", page_icon="♻️", layout="centered")
st.markdown("<h1 style='text-align: center; color: green;'>♻️ Klasifikasi Sampah</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Deteksi apakah sampah merupakan <b>Metal</b> atau <b>Non Metal</b>.</p>", unsafe_allow_html=True)
st.markdown("---")

# Menampilkan gambar dari ESP32
st.subheader("Gambar dari ESP32-CAM")
url = "https://1e7c-114-10-145-57.ngrok-free.app/get_image"

# Tempat untuk menampilkan gambar dari ESP32
image_placeholder = st.empty()

try:
    # Request gambar dari ESP32 setiap 5 detik
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            # Menangani gambar sebagai file gambar
            img = Image.open(BytesIO(response.content))  # Menggunakan BytesIO untuk menangani konten gambar biner
            image_placeholder.image(img, caption="📸 Gambar dari ESP32", use_container_width=True)

            # Prediksi gambar
            label, confidence, raw_pred = predict_image(img)
            st.success(f"🎯 Prediksi: {label}")
            st.write(f"📊 Confidence: **{confidence*100:.2f}%**")

            if label == "Metal":
                st.info("🔩 Kategori Metal: kaleng, besi, aluminium, dll.")
            else:
                st.info("🧴 Kategori Non Metal: plastik, kertas, kain, dll.")

            # Menambahkan ke riwayat prediksi
            st.session_state.history.append({
                "filename": "Gambar ESP32",
                "label": label,
                "confidence": f"{confidence*100:.2f}%",
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            })

            # Mengirim prediksi ke ESP32
            send_prediction_to_esp32(label, confidence)

        else:
            st.warning("🚫 Gagal mengambil gambar dari ESP32.")
        
        time.sleep(5)  # Menunggu selama 5 detik sebelum melakukan request lagi

except Exception as e:
    st.error(f"❌ Error: {e}")

# Menampilkan riwayat prediksi
st.markdown("---")
if st.session_state.history:
    st.subheader("🕒 Riwayat Prediksi")
    with st.expander("Lihat Riwayat"):
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            st.write(f"**{i}.** `{item['filename']}` - {item['label']} ({item['confidence']}) 🕔 {item['timestamp']}")

# Menampilkan grafik pie distribusi kategori sampah
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

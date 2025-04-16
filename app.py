import streamlit as st
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import datetime
import os

# Load model
model = load_model("model_sampah_metal_vs_non_metal_optimal.h5")

# Inisialisasi session_state untuk menyimpan riwayat
if "history" not in st.session_state:
    st.session_state.history = []

# Fungsi prediksi
def predict_image(img, threshold=0.5):
    img = img.resize((150, 150))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array)[0][0]
    label = "Non Metal" if prediction > threshold else "Metal"
    confidence = prediction if prediction > threshold else 1 - prediction
    return label, confidence, prediction

# Judul halaman
st.set_page_config(page_title="Klasifikasi Sampah")
st.title("Klasifikasi Sampah - Metal vs Non-Metal")
st.markdown("Upload gambar sampah untuk diprediksi apakah itu logam atau non-logam.")

# Threshold slider
threshold = st.slider("Atur Threshold Confidence", 0.0, 1.0, 0.5, 0.01)

# ------------------------------
# 🔹 Bagian 1: Upload Manual
# ------------------------------
st.markdown("### Upload Gambar Manual")
uploaded_file = st.file_uploader("Unggah gambar dari komputer", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Gambar yang Diunggah", use_column_width=True)
    
    label, confidence, raw_pred = predict_image(image, threshold)

    st.success(f"Prediksi: {label}")
    st.write(f"Confidence: {confidence*100:.2f}%")

    if label == "Metal":
        st.info("Kategori Metal: contoh seperti kaleng, besi, aluminium, dan lainnya.")
    else:
        st.info("Kategori Non Metal: contoh seperti plastik, kertas, kain, dan lainnya.")

    st.session_state.history.append({
        "filename": uploaded_file.name,
        "label": label,
        "confidence": f"{confidence*100:.2f}%",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })

# ------------------------------
# 🔹 Bagian 2: Gambar Otomatis dari ESP32-CAM
# ------------------------------
st.markdown("### Gambar dari ESP32-CAM (Otomatis)")

# Ambil file gambar yang dimulai dengan "upload_" dan berekstensi .jpg
esp32_images = [f for f in os.listdir(".") if f.startswith("upload_") and f.endswith(".jpg")]
esp32_images = sorted(esp32_images, reverse=True)

if esp32_images:
    latest_image_path = esp32_images[0]
    latest_image = Image.open(latest_image_path)
    st.image(latest_image, caption=f"Gambar ESP32: {latest_image_path}", use_column_width=True)

    if st.button("Prediksi Gambar ESP32 Terbaru"):
        label, confidence, raw_pred = predict_image(latest_image, threshold)

        st.success(f"Prediksi: {label}")
        st.write(f"Confidence: {confidence*100:.2f}%")

        if label == "Metal":
            st.info("Kategori Metal: contoh seperti kaleng, besi, aluminium, dan lainnya.")
        else:
            st.info("Kategori Non Metal: contoh seperti plastik, kertas, kain, dan lainnya.")

        st.session_state.history.append({
            "filename": latest_image_path,
            "label": label,
            "confidence": f"{confidence*100:.2f}%",
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        })
else:
    st.warning("Belum ada gambar dari ESP32-CAM.")

# ------------------------------
# 🔹 Bagian 3: Riwayat Prediksi
# ------------------------------
if st.session_state.history:
    with st.expander("Riwayat Prediksi"):
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            st.write(f"{i}. {item['filename']} - {item['label']} ({item['confidence']}) pada {item['timestamp']}")

# ------------------------------
# 🔹 Bagian 4: Tentang Aplikasi
# ------------------------------
with st.expander("Tentang Aplikasi"):
    st.markdown("""
    - Model: CNN dengan transfer learning
    - Dikembangkan untuk mengklasifikasikan sampah Metal vs Non-Metal
    - Dibuat oleh Kelompok Tim Semangat Lomba
    - Framework: TensorFlow dan Streamlit
    """)

st.markdown("---")
st.caption("© 2025 | Dibuat oleh Kelompok Tim Semangat Lomba")

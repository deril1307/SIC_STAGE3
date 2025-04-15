import streamlit as st
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import requests
from io import BytesIO

# Load model
model = load_model("model_sampah_metal_vs_non_metal_optimal.h5")

# Fungsi prediksi gambar
def predict_image(img):
    img = img.resize((150, 150))  # Resize sesuai input model
    img_array = np.array(img) / 255.0  # Normalisasi
    img_array = np.expand_dims(img_array, axis=0)  # (1, 150, 150, 3)
    prediction = model.predict(img_array)[0][0]
    label = "♻️ Metal" if prediction > 0.5 else "🗑️ Non-Metal"
    confidence = prediction if prediction > 0.5 else 1 - prediction
    return label, confidence

# UI Streamlit
st.title("📸 Klasifikasi Sampah - Metal vs Non-Metal")

# Pilihan input: Upload gambar / URL ESP32-CAM
option = st.radio("Pilih sumber gambar:", ["Upload Gambar", "ESP32-CAM"])

if option == "Upload Gambar":
    uploaded_file = st.file_uploader("Unggah gambar sampah", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar yang Diunggah", use_column_width=True)
        label, confidence = predict_image(image)
        st.success(f"Prediksi: **{label}** (Confidence: {confidence*100:.2f}%)")

elif option == "ESP32-CAM":
    cam_url = st.text_input("Masukkan URL ESP32-CAM (contoh: http://192.168.4.1/cam.jpg)")
    if st.button("Ambil Gambar"):
        try:
            response = requests.get(cam_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption="Gambar dari ESP32-CAM", use_column_width=True)
            label, confidence = predict_image(img)
            st.success(f"Prediksi: **{label}** (Confidence: {confidence*100:.2f}%)")
        except:
            st.error("❌ Gagal mengambil gambar dari ESP32-CAM")


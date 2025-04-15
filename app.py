import streamlit as st
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import datetime

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

# Upload gambar
uploaded_file = st.file_uploader("Unggah gambar", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Gambar yang Diunggah", use_column_width=True)
    
    label, confidence, raw_pred = predict_image(image, threshold)

    st.success(f"Prediksi: {label}")
    st.write(f"Confidence: {confidence*100:.2f}%")

    # Informasi tambahan sesuai label
    if label == "Metal":
        st.info("Kategori Metal: contoh seperti kaleng, besi, aluminium, dan lainnya.")
    else:
        st.info("Kategori Non Metal: contoh seperti plastik, kertas, kain, dan lainnya.")

    # Simpan ke riwayat
    st.session_state.history.append({
        "filename": uploaded_file.name,
        "label": label,
        "confidence": f"{confidence*100:.2f}%",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })

# Tampilkan riwayat prediksi
if st.session_state.history:
    with st.expander("Riwayat Prediksi"):
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            st.write(f"{i}. {item['filename']} - {item['label']} ({item['confidence']}) pada {item['timestamp']}")

# Info tentang aplikasi
with st.expander("Tentang Aplikasi"):
    st.markdown("""
    - Model: CNN dengan transfer learning
    - Dikembangkan untuk mengklasifikasikan sampah Metal vs Non-Metal
    - Dibuat oleh Deril Wijdan Falih
    - Framework: TensorFlow dan Streamlit
    """)

st.markdown("---")
st.caption("© 2025 | Dibuat oleh Deril")

from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
import time
import threading

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

latest_prediction = {
    "label": None,
    "confidence": None,
    "timestamp": None
}

# Variabel untuk menyimpan waktu terakhir upload
last_upload_time = None
UPLOAD_TIMEOUT = 10  # detik

# Fungsi background untuk memantau timeout
def auto_delete_image_if_idle():
    global last_upload_time
    while True:
        time.sleep(3)  # cek setiap 3 detik
        if last_upload_time:
            elapsed = time.time() - last_upload_time
            if elapsed > UPLOAD_TIMEOUT:
                for filename in os.listdir(UPLOAD_FOLDER):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"[INFO] Gambar {filename} dihapus otomatis setelah {UPLOAD_TIMEOUT} detik tidak ada upload")
                last_upload_time = None

@app.route("/upload", methods=["POST"])
def upload_image():
    global last_upload_time

    # Hapus semua gambar lama
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Simpan gambar baru
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upload_{timestamp}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        f.write(request.data)

    last_upload_time = time.time()
    print(f"[INFO] Gambar disimpan: {filename}")
    return "Gambar diterima", 200

@app.route("/prediksi", methods=["POST"])
def receive_prediction():
    global latest_prediction
    data = request.json
    label = data.get("label")
    confidence = data.get("confidence")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    latest_prediction = {
        "label": label,
        "confidence": confidence,
        "timestamp": timestamp
    }

    print(f"[INFO] Prediksi diterima: Label = {label}, Confidence = {confidence}")
    return jsonify({"status": "success", "received": latest_prediction}), 200

@app.route("/get_image", methods=["GET"])
def get_image():
    esp32_images = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith((".jpg", ".png"))]
    esp32_images = sorted(esp32_images, reverse=True)
    if esp32_images:
        latest_image_filename = esp32_images[0]
        return send_from_directory(UPLOAD_FOLDER, latest_image_filename)
    else:
        return jsonify({"status": "no_image"}), 404

@app.route("/latest", methods=["GET"])
def get_latest_prediction():
    if latest_prediction["label"] is None:
        return jsonify({"status": "no_prediction"}), 404
    return jsonify(latest_prediction), 200

if __name__ == "__main__":
    # Jalankan thread pemantauan sebelum start Flask
    monitor_thread = threading.Thread(target=auto_delete_image_if_idle, daemon=True)
    monitor_thread.start()

    app.run(host="0.0.0.0", port=5000)

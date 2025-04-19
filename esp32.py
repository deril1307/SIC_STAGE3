from machine import Pin, time_pulse_us, PWM
import time
from hx711 import HX711
import network
import urequests

# === Konfigurasi Sensor Ultrasonik ===
trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)

def baca_jarak():
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()

    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None
    distance = (duration * 0.0343) / 2
    return distance

# === Load Cell HX711 ===
hx = HX711(d_out=Pin(21), pd_sck=Pin(22))

# === Servo Motor ===
servo = PWM(Pin(15), freq=50)

def atur_servo(angle):
    min_duty = 40   # 0 derajat
    max_duty = 115  # 180 derajat
    duty = min_duty + int((max_duty - min_duty) * angle / 180)
    servo.duty(duty)

# === Koneksi WiFi ===
def connect_wifi():
    wifi_ssid = 'Tes'          
    wifi_password = '12345678' 

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_ssid, wifi_password)

    while not wlan.isconnected():
        time.sleep(1)
    print('Terhubung ke WiFi')
    print(wlan.ifconfig())

# === Ambil Prediksi dari Server Flask ===
def get_latest_prediction():
    try:
        response = urequests.get("https://1e7c-114-10-145-57.ngrok-free.app/latest") 
        if response.status_code == 200:
            data = response.json()
            print("Prediksi Sampah:")
            print("Label:", data["label"])
            print("Confidence:", data["confidence"])
            print("Waktu:", data["timestamp"])
            return data
        else:
            print("Belum ada prediksi.")
    except:
        print("Gagal terhubung ke server prediksi.")
    return None

# === Kirim Data ke Ubidots ===
UBIDOTS_TOKEN = "BBUS-mzlEnMdMD0suNuMSCuVqs9bv27vckv"
DEVICE_LABEL = "pemilahansampah"

def kirim_ke_ubidots(distance, weight, label):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/" + DEVICE_LABEL
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }

    material_value = 1 if label == "metal" else 0

    payload = {
        "distance": distance,
        "weight": weight,
        "material_type": material_value
    }

    try:
        response = urequests.post(url, json=payload, headers=headers)
        print("Status kirim ke Ubidots:", response.status_code)
        response.close()
    except Exception as e:
        print("Gagal kirim ke Ubidots:", e)

# === Fungsi untuk Membaca Berat ===
def baca_berat():
    return hx.read()

# === Inisialisasi ===
connect_wifi()
hx.set_scale(1500)
hx.tare()  
atur_servo(90)
last_timestamp = None

# === Threshold Berat Minimum ===
THRESHOLD_BERAT = 50  

# === Loop Utama ===
while True:
    # Ambil Prediksi
    prediksi = get_latest_prediction()
    if prediksi:
        current_timestamp = prediksi["timestamp"]

        if current_timestamp != last_timestamp:
            last_timestamp = current_timestamp
            label = prediksi["label"].lower()
            print("Prediksi Baru:", label)

            # Baca Berat
            berat_raw = baca_berat()
            gram = berat_raw / 1000.0

            if gram < THRESHOLD_BERAT:
                gram = 0
            else:
                gram = gram - THRESHOLD_BERAT + 1

            print("Berat Sampah: {:.2f} gram".format(gram))

            # Kontrol Servo
            if label == "metal":
                print("Servo ke kanan (metal)")
                atur_servo(0)
            elif label == "non metal":
                print("Servo ke kiri (non-metal)")
                atur_servo(180)
            else:
                print("Label tidak dikenali. Servo tidak digerakkan.")

            time.sleep(2)
            atur_servo(90)

            # Baca Jarak
            jarak = baca_jarak()
            if jarak is not None:
                print("Jarak Sampah: {:.2f} cm".format(jarak))
            else:
                print("Gagal membaca jarak.")
                jarak = 0

            # Kirim ke Ubidots
            kirim_ke_ubidots(jarak, gram, label)
        else:
            print("Belum ada sampah terbaru")
    time.sleep(3)

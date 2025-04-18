import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from tensorflow.keras.applications import VGG16
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Augmentasi Data (disesuaikan untuk dataset besar agar tidak overfitting atau noisy)
train_datagen = ImageDataGenerator(
    rescale=1./255,  # Normalisasi gambar
    rotation_range=20,  # Rotasi gambar
    width_shift_range=0.1,  # Perubahan posisi horizontal
    height_shift_range=0.1,  # Perubahan posisi vertikal
    shear_range=0.1,  # Shear transformasi
    zoom_range=0.2,  # Zoom in/out
    horizontal_flip=True,  # Flip horizontal
    fill_mode='nearest',  # Mengisi bagian kosong pada gambar
    brightness_range=[0.8, 1.2],  # Meningkatkan variasi pencahayaan
    validation_split=0.2  # Memisahkan data validasi
)

# 2. Path Dataset
train_dir = 'dataset/train'
test_dir = 'dataset/test'

# 3. Generator Training & Validation
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),  # Mengubah ukuran gambar
    batch_size=32,
    class_mode='binary',  # Klasifikasi biner
    subset='training'
)

val_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),  # Ukuran gambar yang sama
    batch_size=32,
    class_mode='binary',  # Klasifikasi biner
    subset='validation'
)

# 4. Load VGG16 tanpa top layer
base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False  # Freeze layer untuk transfer learning awal

# 5. Bangun Model
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(256, activation='relu', kernel_regularizer=l2(0.001)),  # Regularisasi L2 untuk menghindari overfitting
    layers.Dropout(0.6),  # Dropout untuk mencegah overfitting
    layers.Dense(1, activation='sigmoid')  # Binary classification (0 atau 1)
])

# 6. Compile Model
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),  # Menggunakan Adam optimizer
    loss='binary_crossentropy',  # Crossentropy loss untuk klasifikasi biner
    metrics=['accuracy']  # Mengukur akurasi
)

# 7. Callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=5, min_lr=1e-6)

# 8. Training Awal (transfer learning)
history = model.fit(
    train_generator,
    epochs=50,
    validation_data=val_generator,
    callbacks=[early_stopping, lr_scheduler]
)

# 9. Fine-Tuning: buka layer terakhir VGG16
base_model.trainable = True
for layer in base_model.layers[:-4]:  # Buka hanya 4 layer terakhir
    layer.trainable = False

# 10. Re-compile setelah unfreeze
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),  # Menggunakan learning rate yang lebih kecil
    loss='binary_crossentropy',  # Loss function untuk klasifikasi biner
    metrics=['accuracy']  # Mengukur akurasi
)

# 11. Fine-tune Training
fine_tune_history = model.fit(
    train_generator,
    epochs=20,
    validation_data=val_generator,
    callbacks=[early_stopping, lr_scheduler]
)

# 12. Simpan Model
model.save('model_sampah_metal_vs_non_metal_final.h5')

# 13. Visualisasi Akurasi & Loss
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'] + fine_tune_history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'] + fine_tune_history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'] + fine_tune_history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'] + fine_tune_history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# 14. Evaluasi pada Data Test
test_datagen = ImageDataGenerator(rescale=1./255)  # Hanya normalisasi gambar pada data uji
test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),  # Ukuran gambar yang sama
    batch_size=32,
    class_mode='binary',  # Klasifikasi biner
    shuffle=False
)

test_loss, test_acc = model.evaluate(test_generator)
print(f"\n✅ Akurasi pada Data Test: {test_acc * 100:.2f}%")

# 15. Confusion Matrix
y_true = test_generator.classes
y_pred = model.predict(test_generator)
y_pred = (y_pred > 0.5).astype(int)  # Binarisasi prediksi untuk 0 atau 1

# Matriks kebingunguan
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()

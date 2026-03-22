import tensorflow as tf
from tensorflow.keras import layers, models
import os

# Dataset path
dataset_path = "dataset"

img_size = 128
batch_size = 16

train_data = tf.keras.preprocessing.image_dataset_from_directory(
    dataset_path,
    image_size=(img_size, img_size),
    batch_size=batch_size,
    color_mode="grayscale",
    label_mode="binary"
)

model = models.Sequential([
    layers.Rescaling(1./255, input_shape=(img_size, img_size, 1)),
    layers.Conv2D(32, (3,3), activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

model.fit(train_data, epochs=25)

# Save model
os.makedirs("models", exist_ok=True)
model.save("models/cnn_signature_model.h5")

print("Model saved successfully!")
import numpy as np
import cv2
from tensorflow.keras.models import load_model

model = load_model("models/cnn_signature_model.h5")

def cnn_predict(image_path):

    img = cv2.imread(image_path, 0)
    img = cv2.resize(img, (128,128))
    img = img / 255.0
    img = img.reshape(1,128,128,1)

    prediction = model.predict(img)

    return float(prediction[0][0])
import os
import urllib.request

MODELS_DIR = "models"
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

models = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "face_anti_spoofing_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_anti_spoofing/face_anti_spoofing_yunet_2023mar.onnx"
}

print("Downloading AI Models...")

for name, url in models.items():
    path = os.path.join(MODELS_DIR, name)
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        try:
            urllib.request.urlretrieve(url, path)
            print("   Done.")
        except Exception as e:
            print(f"   Error downloading {name}: {e}")
    else:
        print(f"   {name} already exists.")

print("All models ready.")

import cv2
import os
import gspread
import pickle
import numpy as np
import time
import faiss
from flask import Flask, render_template, request, jsonify
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# --- CONFIG ---
DATASET_PATH = 'dataset'
ENCODINGS_FILE = 'encodings.pickle'
SHEET_ID = "1kMbG_96D552CcXQcijLVH8ggFQxN8qLRbZdL1N-6oTc"
DETECTION_MODEL = "models/face_detection_yunet_2023mar.onnx"
RECOGNITION_MODEL = "models/face_recognition_sface_2021dec.onnx"

# Anti-Spam Cache
recently_marked = {}
COOLDOWN_SECONDS = 60

# Liveness / Blink Config
liveness_verified = False # Default to False if MP works, True if disabled
blink_enabled = True # Flag to check if we should run blink logic
blink_counter = 0
last_blink_time = 0
BLINK_CONSEC_FRAMES = 1

last_name = "Scanning..."
last_time = "--:--:--"
last_date = "--/--/----"

# Google Sheets Setup
sheet = None # Initialize as None

# Load Credentials from File OR Environment Variable (Render Secret)
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if os.path.exists("credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    else:
        # For Render: Create the file from Environment Variable
        import json
        google_creds = os.environ.get("GOOGLE_CREDENTIALS")
        if google_creds:
            creds_dict = json.loads(google_creds)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            raise FileNotFoundError("credentials.json not found and GOOGLE_CREDENTIALS env var not set")

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    print("✅ Google Sheets Connected")
except Exception as e:
    print(f"⚠️ Sheets Error: {e}")

# ... (Rest of AI Setup remains same) ...

# (Bottom of file)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- AI SETUP ---
print("🚀 Loading AI Models...")
detector = cv2.FaceDetectorYN.create(DETECTION_MODEL, "", (320, 320), 0.9, 0.3, 5000)
recognizer = cv2.FaceRecognizerSF.create(RECOGNITION_MODEL, "")

# MediaPipe Setup (With Safety Check)
mp_face_mesh = None
face_mesh = None

try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("✅ MediaPipe Loaded (Blink Detection Active)")
except Exception as e:
    print(f"⚠️ MediaPipe Error: {e}")
    print("⚠️ Disabling Blink Detection (Running in Standard Mode)")
    blink_enabled = False
    liveness_verified = True # Bypass liveness

# FAISS Index
index = None
known_names = []
known_embeddings = []

if os.path.exists(ENCODINGS_FILE):
    try:
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
            known_embeddings = data["embeddings"]
            known_names = data["names"]
            
        if known_embeddings:
            embeddings_np = np.array(known_embeddings).astype('float32')
            faiss.normalize_L2(embeddings_np)
            index = faiss.IndexFlatL2(128)
            index.add(embeddings_np)
            print(f"✅ FAISS Index Built! {len(known_names)} vectors.")
    except Exception as e:
        print(f"❌ Error loading encodings: {e}")

if index is None:
    index = faiss.IndexFlatL2(128)

def normalize_vector(v):
    norm = np.linalg.norm(v)
    if norm == 0: return v
    return v / norm

def calculate_ear(landmarks, width, height):
    # Helper to get coords
    def get_coords(idx):
        return np.array([landmarks[idx].x * width, landmarks[idx].y * height])

    # Left Eye
    p1_l = get_coords(159)
    p2_l = get_coords(145)
    p3_l = get_coords(33)
    p4_l = get_coords(133)
    vertical_dist_l = np.linalg.norm(p1_l - p2_l)
    horizontal_dist_l = np.linalg.norm(p3_l - p4_l)
    ratio_l = vertical_dist_l / horizontal_dist_l

    # Right Eye
    p1_r = get_coords(386)
    p2_r = get_coords(374)
    p3_r = get_coords(362)
    p4_r = get_coords(263)
    vertical_dist_r = np.linalg.norm(p1_r - p2_r)
    horizontal_dist_r = np.linalg.norm(p3_r - p4_r)
    ratio_r = vertical_dist_r / horizontal_dist_r

    return (ratio_l + ratio_r) / 2.0

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    global last_name, last_time, last_date, blink_counter, liveness_verified, last_blink_time

    file = request.files['frame']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None: return jsonify({"name": "Error", "faces": []})

    h, w, _ = img.shape
    detector.setInputSize((w, h))

    # 1. BLINK DETECTION (Only if enabled)
    if blink_enabled:
        # Expire liveness
        if liveness_verified and (time.time() - last_blink_time > 10):
            liveness_verified = False
            
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_img)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                ear = calculate_ear(face_landmarks.landmark, w, h)
                if ear < 0.22:
                    blink_counter += 1
                else:
                    if blink_counter >= BLINK_CONSEC_FRAMES:
                        liveness_verified = True
                        last_blink_time = time.time()
                    blink_counter = 0

    # 2. FACE RECOGNITION
    _, faces = detector.detect(img)
    response_faces = []
    
    # UI Name Display Logic
    if liveness_verified:
        current_name = "Scanning..."
    else:
        current_name = "PLEASE BLINK"

    if faces is not None:
        for face in faces:
            box_x, box_y, box_w, box_h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            
            name = "Unknown"
            
            # Check Liveness
            if liveness_verified:
                align_face = recognizer.alignCrop(img, face)
                feature = recognizer.feature(align_face)
                feature = normalize_vector(feature) # Normalize query

                if index.ntotal > 0:
                    query = np.array([feature[0]]).astype('float32')
                    faiss.normalize_L2(query) # Double check normalization for FAISS input
                    D, I = index.search(query, 1)
                    
                    if D[0][0] < 1.1:
                        name = known_names[I[0][0]]
                        
                        # Attendance Logic
                        if time.time() - recently_marked.get(name, 0) > COOLDOWN_SECONDS:
                            now = datetime.now()
                            t_str, d_str = now.strftime('%H:%M:%S'), now.strftime('%d-%m-%Y')
                            
                            # UI Updates First (Ensure these happen regardless of Sheet)
                            print(f"✅ Attendance: {name}")
                            recently_marked[name] = time.time()
                            last_name, last_time, last_date = name, t_str, d_str
                            current_name = name
                            
                            # Try Sheet Update
                            if sheet:
                                try:
                                    sheet.append_row([name, t_str, d_str])
                                except Exception as e:
                                    print(f"⚠️ Sheet Upload Failed: {e}")
                            else:
                                print(f"⚠️ Skipping Sheet Upload (No Credentials)")
                        else:
                            current_name = name
            else:
                name = "Blink to Verify"
                current_name = "Blink to Verify"

            response_faces.append({
                "x": box_x, "y": box_y, "w": box_w, "h": box_h,
                "name": name
            })

    return jsonify({
        "name": last_name if (last_name != "Scanning..." and liveness_verified) else current_name,
        "time": last_time,
        "date": last_date,
        "faces": response_faces,
        "liveness": liveness_verified
    })

@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form['name']
        file = request.files['frame']
        
        # In-Memory Processing (No file saved to disk)
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"status": "error", "message": "Failed to decode image"})

        h, w, _ = img.shape
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)
        
        if faces is not None:
            face = faces[0]
            align_face = recognizer.alignCrop(img, face)
            feature = recognizer.feature(align_face)
            feature = normalize_vector(feature) # Normalize on registration
            
            vector = np.array([feature[0]]).astype('float32')
            faiss.normalize_L2(vector)
            index.add(vector)
            
            known_embeddings.append(feature[0])
            known_names.append(name)
            
            data = {"embeddings": known_embeddings, "names": known_names}
            with open(ENCODINGS_FILE, "wb") as f: pickle.dump(data, f)
                
            return jsonify({"status": "success", "message": f"User {name} registered!"})
        else:
            return jsonify({"status": "error", "message": "No face detected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
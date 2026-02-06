# 👁️ Privacy-First AI Face Attendance System

A professional, secure, and deployment-ready Face Attendance System that uses **Memory-Only Processing** to ensure user privacy while delivering high-speed recognition using FAISS.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![OpenCV](https://img.shields.io/badge/Vision-OpenCV-red)
![Docker](https://img.shields.io/badge/Deploy-Docker-blue)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🚀 How It Works (The Core Logic)

This system is different from traditional face recognition apps because it **never saves user photos to the disk**.

1.  **Capture 📸**: The browser (`script.js`) captures a video frame and sends it to the server.
2.  **In-Memory Processing 🧠**: The server (`app.py`) reads the image into RAM.
3.  **Vectorization 🔢**:
    *   **Detection**: OpenCV `YuNet` finds the face.
    *   **Recognition**: OpenCV `SFace` converts the face into a **128-dimensional vector** (a list of 128 unique numbers representing facial features).
4.  **Privacy Action 🗑️**: The original image is **immediately deleted/discarded** from memory. It is never saved.
5.  **Search 🔍**: The vector is normalized and compared against the database using **FAISS** (Facebook AI Similarity Search) to find a match in < 1ms.
6.  **Logging �**: If a match is found, attendance is logged to **Google Sheets**.

---

## 🛠️ Dependencies & Tech Stack

### Core Frameworks
*   **Python 3.9+**: The programming language.
*   **Flask**: The web server handling HTTP requests.
*   **Gunicorn**: Production-grade server for deployment.

### Artificial Intelligence
*   **OpenCV (opencv-contrib-python)**:
    *   `FaceDetectorYN`: State-of-the-art face detection.
    *   `FaceRecognizerSF`: High-accuracy recognition model.
*   **MediaPipe**: Google's machine learning library used for **Blink Detection** (Anti-Spoofing).
*   **FAISS (faiss-cpu)**: A library for efficient similarity search of dense vectors.

### Data & Integration
*   **gspread**: API client for Google Sheets.
*   **oauth2client**: Authentication for Google Cloud.
*   **NumPy**: High-performance mathematical operations.

---

## 📂 Project Structure

```text
/
├── app.py                # The main application logic (Backend)
├── Dockerfile            # Instructions for Cloud Deployment
├── requirements.txt      # List of all dependencies
├── runtime.txt           # Python version for Render
├── credentials.json      # (You must create this) Google Cloud Keys
├── encodings.pickle      # The database of registered face vectors
├── models/               # directory containing ONNX AI models
├── static/
│   └── script.js         # Frontend Logic (Camera, API calls)
└── templates/
    └── index.html        # The Dashboard UI
```

---

## � How to Run Locally

### Prerequisites
1.  Python 3.9 or higher installed.
2.  A Google Cloud Service Account JSON key (renamed to `credentials.json`).

### Step 1: Install
```bash
# Clone the repository
git clone https://github.com/your-repo/attendance-system.git
cd attendance-system

# Install requirements
pip install -r requirements.txt
```

### Step 2: Configure
1.  Place your `credentials.json` file in the root folder.
2.  Open `app.py` and update the `SHEET_ID` variable with your Google Sheet ID.
3.  Share your Google Sheet with the `client_email` found inside your json key.

### Step 3: Run
```bash
python app.py
```
*   The app will start at `http://127.0.0.1:5000`.
*   Allow Camera access when prompted.

---

## ☁️ How to Deploy (Render.com)

This project is fully configured for **Render**.

1.  **Push to GitHub**: Upload this folder to a GitHub repository.
2.  **Create New Web Service**:
    *   Go to [Render Dashboard](https://dashboard.render.com/).
    *   Click **New +** -> **Web Service**.
    *   Connect your GitHub repository.
3.  **Settings**:
    *   **Runtime**: Select **Docker**.
    *   **Region**: Choose closest to you.
4.  **Environment Variables**:
    *   **Key**: `GOOGLE_CREDENTIALS`
    *   **Value**: Copy and paste the *entire content* of your `credentials.json`.
5.  **Deploy**: Click "Create Web Service".

> **⚠️ Important Data Note**: On the free tier of Render, the file system is ephemeral. This means `encodings.pickle` (registered users) will be reset if the server restarts. To fix this, upgrade to a paid plan with a **Persistent Disk**. Your Google Sheet logs will always be safe.

---

## �️ Security Features
*   **Anti-Spoofing**: If MediaPipe is compatible, users must **BLINK** to verify they are real (prevents using photos to cheat).
*   **Data Minimization**: No biometric images are stored, reducing liability using a privacy-first architecture.

---
© 2026 AI Vision Systems

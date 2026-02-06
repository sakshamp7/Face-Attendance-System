const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const captureCanvas = document.getElementById('captureCanvas');
const captureCtx = captureCanvas.getContext('2d');

const nameEl = document.getElementById('name');
const timeEl = document.getElementById('time');
const dateEl = document.getElementById('date');

// Access Camera
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Camera access denied:", err);
        nameEl.innerText = "Camera Access Denied";
        nameEl.classList.add("text-danger");
    });

// Process frames for recognition (0.4 FPS)
setInterval(() => {
    if (video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Match canvas size to video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;

    // Draw video to hidden canvas
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

    // Convert to Blob (JPEG)
    captureCanvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('frame', blob);

        // Send to backend
        fetch('/recognize', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                // Clear previous drawings
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Mirror drawing for natural feel
                ctx.save();
                ctx.scale(-1, 1);
                ctx.translate(-canvas.width, 0);

                // Update stats
                if (data.name !== "Unknown" && data.name !== "Scanning...") {
                    nameEl.innerText = data.name;
                    nameEl.classList.remove('text-primary');
                    nameEl.classList.add('text-success');
                    timeEl.innerText = data.time || "--:--:--";
                    dateEl.innerText = data.date || "--/--/----";
                } else {
                    nameEl.innerText = data.name;
                    nameEl.classList.remove('text-success');
                    nameEl.classList.add('text-primary');
                }

                // Draw faces
                data.faces.forEach(face => {
                    const { x, y, w, h, name } = face;
                    const color = name !== "Unknown" ? "#00ff00" : "#0000ff";

                    // Draw Box
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 3;
                    ctx.strokeRect(x, y, w, h);

                    // Draw Name
                    ctx.fillStyle = color;
                    ctx.font = "bold 20px Arial";
                    ctx.fillText(name, x, y - 10);
                });

                ctx.restore();
            })
            .catch(err => console.error("Error:", err));
    }, 'image/jpeg', 0.8);

}, 2500); // 0.4 FPS (Optimized for speed)

// Registration Logic
function registerUser() {
    const name = document.getElementById("username").value.trim();
    if (!name) {
        alert("Please enter a name first!");
        return;
    }

    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        alert("Camera not ready. Please wait.");
        return;
    }

    // Capture Frame
    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

    captureCanvas.toBlob(blob => {
        const formData = new FormData();
        formData.append("frame", blob);
        formData.append("name", name);

        // Disable button while processing
        const btn = document.querySelector(".btn-register");
        btn.innerText = "Registering...";
        btn.disabled = true;

        fetch("/register", {
            method: "POST",
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                alert(data.message || "Registration status unknown");
                if (data.status === "success") {
                    document.getElementById("username").value = "";
                }
            })
            .catch(err => {
                console.error("Registration Error:", err);
                alert("Error: " + err);
            })
            .finally(() => {
                btn.innerText = "Capture & Register";
                btn.disabled = false;
            });

    }, "image/jpeg", 0.95);
}

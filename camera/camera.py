import cv2
import requests
import time
import threading

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


# ============================================================================
# CONFIGURATION
# ============================================================================

CAMERA_INDEX = 0
AI_URL = "http://127.0.0.1:8001/detect"
# Intervalle entre deux analyses IA
ANALYSIS_INTERVAL = 1.0
JPEG_QUALITY = 80


# ============================================================================
# APPLICATION
# ============================================================================

app = FastAPI(
    title="Sentinel-X Camera",
    description="Flux vidéo et surveillance Sentinel-X",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# WEBCAM
# ============================================================================

camera = cv2.VideoCapture(CAMERA_INDEX)

if not camera.isOpened():
    raise RuntimeError(
        "Impossible d'ouvrir la webcam."
    )


# ============================================================================
# ÉTAT DE L'IA
# ============================================================================

detections = []
person_detected = False
persons_count = 0
ai_available = False

lock = threading.Lock()


# ============================================================================
# IMAGE POUR L'IA
# ============================================================================

latest_frame = None
frame_lock = threading.Lock()


# ============================================================================
# ANALYSE IA
# ============================================================================

def ai_worker():

    global detections
    global person_detected
    global persons_count
    global ai_available

    while True:

        # ------------------------------------------------------------
        # Récupérer la dernière image disponible
        # ------------------------------------------------------------

        with frame_lock:

            if latest_frame is None:
                frame = None
            else:
                frame = latest_frame.copy()

        if frame is None:

            time.sleep(0.1)
            continue

        # ------------------------------------------------------------
        # Encoder l'image
        # ------------------------------------------------------------

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
        )

        if not success:

            time.sleep(ANALYSIS_INTERVAL)
            continue

        files = {
            "file": (
                "camera.jpg",
                buffer.tobytes(),
                "image/jpeg",
            )
        }

        # ------------------------------------------------------------
        # Appel YOLO
        # ------------------------------------------------------------

        try:

            response = requests.post(
                AI_URL,
                files=files,
                timeout=2,
            )

            if response.status_code != 200:

                print(
                    f"[AI] Erreur HTTP : "
                    f"{response.status_code}"
                )

                with lock:
                    ai_available = False

            else:

                result = response.json()

                with lock:

                    detections = result.get(
                        "detections",
                        []
                    )

                    person_detected = result.get(
                        "person_detected",
                        False
                    )

                    persons_count = result.get(
                        "persons_count",
                        0
                    )

                    ai_available = True

                # ----------------------------------------------------
                # Logs
                # ----------------------------------------------------

                if person_detected:

                    print(
                        f"[SECURITE] "
                        f"{persons_count} personne(s) "
                        f"détectée(s)"
                    )

                else:

                    print(
                        "[SECURITE] "
                        "Aucune personne détectée."
                    )

        except requests.exceptions.RequestException as exc:

            print(
                f"[AI] Erreur de connexion : {exc}"
            )

            with lock:
                ai_available = False

        # ------------------------------------------------------------
        # Attendre avant la prochaine analyse
        # ------------------------------------------------------------

        time.sleep(ANALYSIS_INTERVAL)


# ============================================================================
# ANNOTATION DE L'IMAGE
# ============================================================================

def annotate_frame(frame):

    with lock:

        current_detections = list(
            detections
        )

        current_person_detected = (
            person_detected
        )

        current_persons_count = (
            persons_count
        )

        current_ai_available = (
            ai_available
        )

    # ----------------------------------------------------------------
    # IA indisponible
    # ----------------------------------------------------------------

    if not current_ai_available:

        cv2.putText(
            frame,
            "IA INDISPONIBLE",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2,
        )

        return frame

    # ----------------------------------------------------------------
    # Bounding boxes
    # ----------------------------------------------------------------

    for detection in current_detections:

        confidence = detection["confidence"]

        box = detection["box"]

        x1 = box["x1"]
        y1 = box["y1"]
        x2 = box["x2"]
        y2 = box["y2"]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            2,
        )

        label = (
            f"PERSONNE "
            f"{confidence:.0%}"
        )

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    # ----------------------------------------------------------------
    # Statut
    # ----------------------------------------------------------------

    if current_person_detected:

        status = (
            f"ALERTE : "
            f"{current_persons_count} personne(s)"
        )

        color = (0, 0, 255)

    else:

        status = "ZONE SECURISEE"

        color = (0, 255, 0)

    cv2.putText(
        frame,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )

    return frame


# ============================================================================
# GÉNÉRATEUR DU FLUX VIDÉO
# ============================================================================

def generate_frames():

    while True:

        # ------------------------------------------------------------
        # Capture webcam
        # ------------------------------------------------------------

        success, frame = camera.read()

        if not success:

            print(
                "[CAMERA] Impossible de récupérer l'image."
            )

            break

        # ------------------------------------------------------------
        # Donner l'image au thread IA
        # ------------------------------------------------------------

        with frame_lock:

            global latest_frame
            latest_frame = frame.copy()

        # ------------------------------------------------------------
        # Annoter avec le dernier résultat IA disponible
        # ------------------------------------------------------------

        display_frame = annotate_frame(
            frame
        )

        # ------------------------------------------------------------
        # Encodage JPEG
        # ------------------------------------------------------------

        success, buffer = cv2.imencode(
            ".jpg",
            display_frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                JPEG_QUALITY,
            ],
        )

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        # ------------------------------------------------------------
        # MJPEG
        # ------------------------------------------------------------

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
def root():

    return {
        "service": "sentinel-camera",
        "status": "running",
        "camera": True,
        "ai": AI_URL,
    }


@app.get("/video_feed")
def video_feed():

    return StreamingResponse(
        generate_frames(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
    )


@app.get("/status")
def status():

    with lock:

        return {
            "ai_available": ai_available,
            "person_detected": person_detected,
            "persons_count": persons_count,
            "detections": detections,
        }


# ============================================================================
# THREAD IA
# ============================================================================

ai_thread = threading.Thread(
    target=ai_worker,
    daemon=True,
)

ai_thread.start()
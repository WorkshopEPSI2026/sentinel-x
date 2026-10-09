import os
import cv2
import json
import requests
import paho.mqtt.client as mqtt
import time
import threading
import subprocess
import imageio_ffmpeg
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


# ============================================================================
# CONFIGURATION
# ============================================================================

# 0 = webcam intégrée du PC, 1 = webcam USB externe (en général)
# Modifiable sans toucher au code : $env:CAMERA_INDEX=2 avant de lancer
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "1"))
# Flux réseau à la place d'une webcam (utile dans Docker) :
#   CAMERA_SOURCE=http://192.168.1.20:8080/video  (ex. appli « IP Webcam » du téléphone)
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "").strip()
AI_URL = os.getenv("AI_URL", "http://127.0.0.1:8001/detect")

# Alertes d'intrusion -> MQTT (même canal que les alertes du boîtier)
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_ALERTS = "sentinel/esp8266/alerts"
CAMERA_ID = os.getenv("CAMERA_ID", "camera-01")
# Fin d'alerte après X secondes sans personne détectée
INTRUSION_CLEAR_S = float(os.getenv("INTRUSION_CLEAR_S", "10"))

ANALYSIS_INTERVAL = 1.0
JPEG_QUALITY = 80

# Dossier de stockage des incidents vidéo
RECORDINGS_DIR = Path(__file__).resolve().parent / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Codec vidéo
VIDEO_CODEC = "mp4v"


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

def open_camera(index):
    """Ouvre la webcam (index) ou un flux réseau (URL)."""
    if isinstance(index, str):
        cam = cv2.VideoCapture(index)
    else:
        # DirectShow sous Windows : plus fiable pour les webcams USB
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cam = cv2.VideoCapture(index, backend)
    if cam.isOpened() and cam.read()[0]:
        return cam
    cam.release()
    return None


if CAMERA_SOURCE:
    CAMERA_INDEX = CAMERA_SOURCE
camera = open_camera(CAMERA_INDEX)

# Webcam USB débranchée -> on se rabat sur la webcam intégrée
if camera is None and not CAMERA_SOURCE and CAMERA_INDEX != 0:
    print(f"[CAMERA] webcam {CAMERA_INDEX} introuvable, utilisation de la webcam 0")
    CAMERA_INDEX = 0
    camera = open_camera(0)

if camera is None:
    raise RuntimeError(
        f"Impossible d'ouvrir la caméra ({CAMERA_SOURCE or CAMERA_INDEX})."
    )

print(f"[CAMERA] caméra utilisée : {CAMERA_INDEX}")


# ============================================================================
# ALERTES D'INTRUSION (MQTT)
# ============================================================================

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CAMERA_ID)
mqtt_client.connect_async(MQTT_HOST, MQTT_PORT)   # ne bloque pas si le broker est absent
mqtt_client.loop_start()

intrusion_active = False
last_person_seen = 0.0


def publish_intrusion(state: str, count: int):
    alert = {
        "device_id": CAMERA_ID,
        "source": "vision",
        "type": "INTRUSION",
        "state": state,
        "value": count,
        "detail": {"persons": count},
    }
    if mqtt_client.is_connected():
        mqtt_client.publish(TOPIC_ALERTS, json.dumps(alert), qos=1)
        print(f"[ALERTE] Intrusion {state} ({count} personne(s))")
    else:
        print(f"[ALERTE] MQTT non connecté ({MQTT_HOST}:{MQTT_PORT}), alerte non envoyée")


def update_intrusion(detected: bool, count: int):
    """TRIGGERED dès qu'une personne apparaît, CLEARED après INTRUSION_CLEAR_S sans personne."""
    global intrusion_active, last_person_seen
    now = time.time()
    if detected:
        last_person_seen = now
        if not intrusion_active:
            intrusion_active = True
            publish_intrusion("TRIGGERED", count)
    elif intrusion_active and now - last_person_seen >= INTRUSION_CLEAR_S:
        intrusion_active = False
        publish_intrusion("CLEARED", 0)


# ============================================================================
# ÉTAT DE L'IA
# ============================================================================

detections = []
person_detected = False
persons_count = 0
ai_available = False

lock = threading.Lock()


# ============================================================================
# ÉTAT DE L'ENREGISTREMENT
# ============================================================================

recording = False
video_writer = None
recording_filename = None
recording_started_at = None

recording_lock = threading.Lock()


def start_recording():
    """
    Démarre un nouvel enregistrement vidéo.
    """

    global recording
    global video_writer
    global recording_filename
    global recording_started_at

    with recording_lock:

        # Un enregistrement est déjà en cours.
        if recording:
            return {
                "recording": True,
                "filename": recording_filename,
                "message": "Enregistrement déjà en cours",
            }

        # Récupérer la résolution réelle de la webcam.
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.get(cv2.CAP_PROP_FPS)

        # Certaines webcams retournent 0 ou une valeur invalide.
        if fps <= 0 or fps > 120:
            fps = 20.0

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        filename = (
            f"incident_{timestamp}.mp4"
        )

        filepath = RECORDINGS_DIR / filename

        fourcc = cv2.VideoWriter_fourcc(
            *VIDEO_CODEC
        )

        writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            fps,
            (width, height),
        )

        if not writer.isOpened():
            raise RuntimeError(
                "Impossible de créer le fichier vidéo."
            )

        video_writer = writer
        recording = True
        recording_filename = filename
        recording_started_at = datetime.now()

        print(
            f"[RECORDING] Démarrage : {filepath}"
        )

        return {
            "recording": True,
            "filename": filename,
            "started_at": recording_started_at.isoformat(),
        }

def convert_to_h264(video_path: Path) -> bool:
    """Convertit une vidéo en H.264 compatible avec les navigateurs."""
    output_path = video_path.with_name(
        f"{video_path.stem}_converted.mp4"
    )

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i", str(video_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-an",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        output_path.replace(video_path)
        print(f"[RECORDING] Vidéo convertie en H.264 : {video_path.name}")
        return True

    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"[RECORDING] Échec de conversion : {exc}")
        output_path.unlink(missing_ok=True)
        return False

def stop_recording():
    """
    Arrête l'enregistrement actuel.
    """

    global recording
    global video_writer
    global recording_filename
    global recording_started_at

    with recording_lock:

        if not recording or video_writer is None:
            return {
                "recording": False,
                "message": "Aucun enregistrement en cours",
            }

        filename = recording_filename
        started_at = recording_started_at

        video_writer.release()

        video_writer = None
        recording = False
        recording_filename = None
        recording_started_at = None

        print(
            f"[RECORDING] Arrêt : {filename}"
        )

        # La conversion s'effectue après la fermeture du fichier.
        filepath = RECORDINGS_DIR / filename
        converted = convert_to_h264(filepath)
        
        return {
            "recording": False,
            "filename": filename,
            "started_at": (
                started_at.isoformat()
                if started_at
                else None
            ),
            "stopped_at": datetime.now().isoformat(),
            "converted_to_h264": converted,
        }



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
                        [],
                    )

                    person_detected = result.get(
                        "person_detected",
                        False,
                    )

                    persons_count = result.get(
                        "persons_count",
                        0,
                    )

                    ai_available = True

                # ----------------------------------------------------
                # Alerte d'intrusion (dashboard -> alertes en cours)
                # ----------------------------------------------------

                update_intrusion(person_detected, persons_count)

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

    global latest_frame

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

            latest_frame = frame.copy()

        # ------------------------------------------------------------
        # Annoter avec le dernier résultat IA disponible
        # ------------------------------------------------------------

        display_frame = annotate_frame(
            frame
        )

        # ------------------------------------------------------------
        # ENREGISTREMENT
        # ------------------------------------------------------------

        with recording_lock:

            if recording and video_writer is not None:

                video_writer.write(display_frame)

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

        ai_state = {
            "ai_available": ai_available,
            "person_detected": person_detected,
            "persons_count": persons_count,
            "detections": detections,
        }

    with recording_lock:

        recording_state = {
            "recording": recording,
            "filename": recording_filename,
            "started_at": (
                recording_started_at.isoformat()
                if recording_started_at
                else None
            ),
        }

    return {
        **ai_state,
        **recording_state,
    }


# ============================================================================
# ENREGISTREMENT
# ============================================================================

@app.post("/recording/start")
def recording_start():

    try:
        return start_recording()

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post("/recording/stop")
def recording_stop():

    return stop_recording()


# ============================================================================
# THREAD IA
# ============================================================================

ai_thread = threading.Thread(
    target=ai_worker,
    daemon=True,
)

ai_thread.start()

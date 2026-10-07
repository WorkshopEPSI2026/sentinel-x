from fastapi import FastAPI, UploadFile, File, HTTPException
from ultralytics import YOLO
from PIL import Image
import io
from datetime import datetime


app = FastAPI(
    title="Sentinel-X AI",
    description="Système de surveillance et détection humaine",
    version="1.0.0"
)


# ==========================================
# MODELE YOLO
# ==========================================

model = YOLO("yolov8n.pt")


# ==========================================
# CONFIGURATION
# ==========================================

CONFIDENCE_THRESHOLD = 0.50

# Classe YOLO correspondant à une personne
PERSON_CLASS = 0


# ==========================================
# ROUTE PRINCIPALE
# ==========================================

@app.get("/")
def root():

    return {
        "service": "Sentinel-X AI",
        "status": "running",
        "model": "YOLOv8n",
        "mode": "human_detection",
        "confidence_threshold": CONFIDENCE_THRESHOLD
    }


# ==========================================
# DETECTION
# ==========================================

@app.post("/detect")
async def detect(file: UploadFile = File(...)):

    # Vérifier que le fichier est une image
    if not file.content_type or not file.content_type.startswith("image/"):

        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être une image."
        )


    # Lire l'image
    image_data = await file.read()


    # Charger l'image
    try:

        image = Image.open(
            io.BytesIO(image_data)
        ).convert("RGB")

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Image invalide."
        )


    # ==========================================
    # ANALYSE YOLO
    # ==========================================

    results = model(image)


    detections = []


    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])


            # ==========================================
            # ON GARDE UNIQUEMENT LES PERSONNES
            # ==========================================

            if class_id != PERSON_CLASS:
                continue


            # Ignorer les détections peu fiables
            if confidence < CONFIDENCE_THRESHOLD:
                continue


            # Coordonnées de la personne
            x1, y1, x2, y2 = box.xyxy[0].tolist()


            detections.append({

                "object": "person",

                "confidence": round(
                    confidence,
                    4
                ),

                "box": {

                    "x1": round(x1),

                    "y1": round(y1),

                    "x2": round(x2),

                    "y2": round(y2)

                }

            })


    # ==========================================
    # RESULTAT
    # ==========================================

    person_detected = len(detections) > 0


    return {

        "success": True,

        "timestamp": datetime.now().isoformat(),

        "person_detected": person_detected,

        "persons_count": len(detections),

        "detections": detections

    }
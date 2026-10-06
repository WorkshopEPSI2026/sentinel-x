from fastapi import FastAPI, UploadFile, File, HTTPException
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="Sentinel-X AI",
    description="API de détection d'objets avec YOLO",
    version="1.0.0"
)

# Chargement du modèle YOLO
model = YOLO("yolov8n.pt")


@app.get("/")
def root():
    return {
        "service": "Sentinel-X AI",
        "status": "running",
        "model": "YOLOv8n"
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...)):

    # Vérification du type de fichier
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être une image"
        )

    # Lecture de l'image reçue
    image_data = await file.read()

    try:
        image = Image.open(io.BytesIO(image_data))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Image invalide"
        )

    # Analyse YOLO
    results = model(image)

    detections = []

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            detections.append({
                "object": model.names[class_id],
                "confidence": round(confidence, 4)
            })

    return {
        "success": True,
        "filename": file.filename,
        "detections": detections
    }
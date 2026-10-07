from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np

app = FastAPI(title="Sentinel-X AI")


@app.get("/")
def root():
    return {"status": "AI service is running"}


@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    data = await file.read()

    image = cv2.imdecode(
        np.frombuffer(data, np.uint8),
        cv2.IMREAD_COLOR
    )

    if image is None:
        return {"success": False, "message": "Image invalide"}

    height, width = image.shape[:2]

    return {
        "success": True,
        "message": "Image reçue par sentinel-ai",
        "width": width,
        "height": height
    }
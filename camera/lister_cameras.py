"""
Liste les webcams détectées par OpenCV et enregistre une photo de chacune.
Usage (dans le dossier camera) :  python lister_cameras.py
Puis ouvrir les fichiers webcam_0.jpg, webcam_1.jpg... pour voir laquelle est la USB.
"""
import os
import cv2

backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
found = False

for i in range(5):
    cam = cv2.VideoCapture(i, backend)
    ok, frame = cam.read() if cam.isOpened() else (False, None)
    if ok:
        found = True
        h, w = frame.shape[:2]
        cv2.imwrite(f"webcam_{i}.jpg", frame)
        print(f"Webcam {i} : OK ({w}x{h}) -> photo enregistrée dans webcam_{i}.jpg")
    else:
        print(f"Webcam {i} : rien")
    cam.release()

if not found:
    print("Aucune webcam détectée.")

import cv2
import requests
import time

AI_URL = "http://localhost:8001/process"

cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Erreur : impossible d'ouvrir la webcam USB")
    exit()

print("Webcam USB ouverte avec succès.")

last_sent = 0
interval = 1  # envoyer une image toutes les 1 seconde

while True:
    ret, frame = cap.read()

    if not ret:
        print("Erreur lors de la récupération de l'image")
        break

    cv2.imshow("Sentinel-X - Webcam", frame)

    current_time = time.time()

    if current_time - last_sent >= interval:
        try:
            success, buffer = cv2.imencode(".jpg", frame)

            if success:
                response = requests.post(
                    AI_URL,
                    files={
                        "file": (
                            "frame.jpg",
                            buffer.tobytes(),
                            "image/jpeg"
                        )
                    },
                    timeout=5
                )

                print("AI :", response.json())

            last_sent = current_time

        except requests.exceptions.RequestException as e:
            print("Erreur de communication avec l'AI :", e)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
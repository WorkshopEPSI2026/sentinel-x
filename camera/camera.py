import cv2
import requests
import time

# Adresse de ton service YOLO
AI_URL = "http://127.0.0.1:8001/detect"

# Ouvre la webcam
camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Erreur : impossible d'ouvrir la webcam.")
    exit()

print("Webcam démarrée.")
print("Une image sera envoyée à YOLO toutes les 1 secondes.")
print("Appuie sur Q pour arrêter.")

last_send = 0

while True:

    # Lire une image de la webcam
    ret, frame = camera.read()

    if not ret:
        print("Erreur : impossible de récupérer l'image.")
        break

    # Afficher la webcam
    cv2.imshow("Sentinel-X - Camera", frame)

    # Temps actuel
    current_time = time.time()

    # Envoyer une image toutes les 1 secondes
    if current_time - last_send >= 1:

        last_send = current_time

        # Convertir l'image en JPEG
        success, buffer = cv2.imencode(".jpg", frame)

        if success:

            files = {
                "file": (
                    "camera.jpg",
                    buffer.tobytes(),
                    "image/jpeg"
                )
            }

            try:

                response = requests.post(
                    AI_URL,
                    files=files,
                    timeout=10
                )

                if response.status_code == 200:

                    result = response.json()

                    print("\n--- Détection YOLO ---")
                    print(result)

                else:

                    print(
                        "Erreur API :",
                        response.status_code
                    )

            except requests.exceptions.RequestException as e:

                print("Erreur de connexion à YOLO :", e)

    # Quitter avec Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()
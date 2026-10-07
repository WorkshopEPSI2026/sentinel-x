import cv2
import requests
import time


# ==========================================
# CONFIGURATION
# ==========================================

AI_URL = "http://127.0.0.1:8001/detect"

ANALYSIS_INTERVAL = 1.0

# Nombre de personnes détectées lors de l'analyse précédente
last_person_count = 0


# ==========================================
# OUVERTURE DE LA WEBCAM
# ==========================================

camera = cv2.VideoCapture(1)


if not camera.isOpened():

    print("Erreur : impossible d'ouvrir la webcam.")

    exit()


print("======================================")
print("        SENTINEL-X SECURITY")
print("======================================")
print("Webcam démarrée.")
print("Mode : détection humaine")
print("Analyse : 1 image / seconde")
print("Appuie sur Q pour arrêter.")
print("======================================")


last_send = 0


# Dernières personnes détectées
detections = []


# ==========================================
# BOUCLE PRINCIPALE
# ==========================================

while True:


    # Lire une image
    ret, frame = camera.read()


    if not ret:

        print(
            "Erreur : impossible de récupérer l'image."
        )

        break


    # ==========================================
    # ANALYSE TOUTES LES 1 SECONDES
    # ==========================================

    current_time = time.time()


    if current_time - last_send >= ANALYSIS_INTERVAL:

        last_send = current_time


        # Convertir l'image en JPEG
        success, buffer = cv2.imencode(
            ".jpg",
            frame
        )


        if success:

            files = {

                "file": (

                    "camera.jpg",

                    buffer.tobytes(),

                    "image/jpeg"

                )

            }


            try:

                # Envoyer à l'IA
                response = requests.post(

                    AI_URL,

                    files=files,

                    timeout=10

                )


                # ==========================================
                # REPONSE DE L'IA
                # ==========================================

                if response.status_code == 200:


                    result = response.json()


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


                    # ==========================================
                    # PERSONNE DETECTEE
                    # ==========================================

                    if person_detected:


                        print()
                        print("🚨 ===============================")
                        print("🚨 ALERTE SENTINEL-X")
                        print("🚨 PERSONNE DETECTEE")
                        print(
                            f"🚨 Nombre de personnes : {persons_count}"
                        )
                        print("🚨 ===============================")


                    else:

                        print(
                            "[SECURITE] "
                            "Aucune personne détectée."
                        )


                    # mémoriser le nombre de personnes
                    last_person_count = persons_count


                else:

                    print(
                        "Erreur API :",
                        response.status_code
                    )


            except requests.exceptions.RequestException as e:

                print(
                    "Erreur de connexion à YOLO :",
                    e
                )


    # ==========================================
    # AFFICHAGE DES PERSONNES
    # ==========================================

    for detection in detections:


        confidence = detection["confidence"]

        box = detection["box"]


        x1 = box["x1"]
        y1 = box["y1"]

        x2 = box["x2"]
        y2 = box["y2"]


        # Rectangle autour de la personne
        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 0, 255),

            2

        )


        # Texte
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

            2

        )


    # ==========================================
    # INFORMATIONS SUR L'ECRAN
    # ==========================================

    if len(detections) > 0:


        status = (
            f"ALERTE : "
            f"{len(detections)} personne(s)"
        )


        cv2.putText(

            frame,

            status,

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 0, 255),

            2

        )


    else:


        cv2.putText(

            frame,

            "ZONE SECURISEE",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 0),

            2

        )


    # ==========================================
    # AFFICHER LA WEBCAM
    # ==========================================

    cv2.imshow(

        "Sentinel-X - Surveillance",

        frame

    )


    # ==========================================
    # QUITTER AVEC Q
    # ==========================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==========================================
# FERMETURE
# ==========================================

camera.release()

cv2.destroyAllWindows()

print()
print("Sentinel-X Security arrêté.")
import cv2

cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Erreur : impossible d'ouvrir la webcam")
    exit()

print("Webcam ouverte avec succès.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Erreur lors de la récupération de l'image")
        break

    cv2.imshow("Sentinel-X - Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
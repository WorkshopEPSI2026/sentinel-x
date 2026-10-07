#!/usr/bin/env python3
"""
Étape 3 : détection en temps réel.

Écoute la télémétrie, garde les WINDOW dernières mesures, calcule les
caractéristiques, demande un score au modèle. Après CONSECUTIVE fenêtres
anormales d'affilée -> alerte ANOMALY TRIGGERED ; retour à la normale -> CLEARED.

L'alerte est publiée sur MQTT (sentinel/esp8266/alerts). Quand le backend aura
une route d'alertes, mettre son URL dans BACKEND_ALERT_URL pour l'y envoyer aussi.

    python detect.py
"""
import json
import os
import time
from collections import deque

import joblib

from config import CONSECUTIVE, MODEL_PATH, MQTT_HOST, MQTT_PORT, TOPIC_ALERTS, TOPIC_TELEMETRY
from features import FEATURE_NAMES, compute_features, is_valid
from mqtt_utils import make_client

BACKEND_ALERT_URL = os.getenv("BACKEND_ALERT_URL")  # ex. http://localhost:8000/api/alerts


def send_alert(client, alert: dict):
    client.publish(TOPIC_ALERTS, json.dumps(alert), qos=1)
    print(f"[ALERTE] {alert['type']} {alert['state']} score={alert['score']}")
    if BACKEND_ALERT_URL:
        try:
            import requests
            requests.post(BACKEND_ALERT_URL, json=alert, timeout=3)
        except Exception as e:  # le backend ne doit pas faire planter la détection
            print(f"[ALERTE] backend injoignable : {e}")


def wait_for_model():
    """En Docker, le conteneur peut démarrer avant l'entraînement : on attend le modèle."""
    while not os.path.exists(MODEL_PATH):
        print(f"[IA] pas encore de modèle ({MODEL_PATH}) : lancez train.py. Nouvel essai dans 10 s")
        time.sleep(10)
    return joblib.load(MODEL_PATH)


def main():
    bundle = wait_for_model()
    model, threshold, window = bundle["model"], bundle["threshold"], bundle["window"]
    print(f"[IA] modèle chargé, fenêtre={window}, seuil={threshold:.4f}")

    buf = deque(maxlen=window)
    state = {"streak": 0, "active": False, "n": 0}

    def on_message(client, userdata, msg):
        try:
            m = json.loads(msg.payload)
        except json.JSONDecodeError:
            return
        if not is_valid(m):
            return
        buf.append({k: float(m[k]) for k in ("temperature", "humidity", "gas")})
        if len(buf) < window:
            if len(buf) % 10 == 0:
                print(f"[IA] remplissage de la fenêtre {len(buf)}/{window}")
            return

        x = compute_features(list(buf))
        score = float(model.decision_function([x])[0])
        anormal = score < threshold
        state["streak"] = state["streak"] + 1 if anormal else 0
        state["n"] += 1
        if state["n"] % 10 == 0 or anormal:
            print(f"[IA] score={score:+.4f} {'ANORMAL' if anormal else 'ok'} "
                  f"T={x[0]:.1f} gaz={x[2]:.0f} pente_gaz={x[4]:+.2f}")

        detail = {name: round(v, 3) for name, v in zip(FEATURE_NAMES, x)}
        base = {"device_id": m.get("device_id", "?"), "source": "ml", "type": "ANOMALY",
                "score": round(score, 4), "ts": time.time()}
        if state["streak"] >= CONSECUTIVE and not state["active"]:
            state["active"] = True
            send_alert(client, {**base, "state": "TRIGGERED", "detail": detail})
        elif state["streak"] == 0 and state["active"]:
            state["active"] = False
            send_alert(client, {**base, "state": "CLEARED", "detail": None})

    c = make_client("sentinel-ia-anomaly")
    c.on_connect = lambda cl, u, fl, rc, p: (cl.subscribe(TOPIC_TELEMETRY),
                                             print(f"[IA] connecté, écoute {TOPIC_TELEMETRY}"))
    c.on_message = on_message
    # connect_async + retry : ne plante pas si le broker démarre après nous
    c.connect_async(MQTT_HOST, MQTT_PORT)
    c.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()

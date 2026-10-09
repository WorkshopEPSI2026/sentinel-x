"""
Service IA « détection d'anomalies » de Sentinel-X.

  MQTT  sentinel/esp8266/telemetry  ->  enregistrement CSV + détection en direct
  MQTT  sentinel/esp8266/alerts     <-  alertes ANOMALY (le backend les stocke
                                        et les pousse au dashboard, rien à changer)
  HTTP  GET  /api/anomaly/status    état du modèle + score en direct (dashboard)
  HTTP  POST /api/anomaly/train     entraîne sur les dernières mesures enregistrées

Lancement : uvicorn main:app --host 0.0.0.0 --port 8002
"""
import csv
import json
import os
import threading
import time

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from detector import MIN_SAMPLES, AnomalyDetector

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_TELEMETRY = os.getenv("TOPIC_TELEMETRY", "sentinel/esp8266/telemetry")
TOPIC_ALERTS = os.getenv("TOPIC_ALERTS", "sentinel/esp8266/alerts")
DATA_PATH = os.getenv("DATA_PATH", "data/telemetry.csv")
# Taille max du fichier : on ne garde que les N dernières mesures
# 20 000 mesures = environ 11 h à 1 mesure / 2 s (~1,1 Mo)
MAX_ROWS = int(os.getenv("MAX_ROWS", "20000"))
TRIM_EVERY = 500          # vérification toutes les 500 mesures
COLUMNS = ["ts", "device_id", "temperature", "humidity", "gas", "presence"]

# Le firmware renvoie une mesure en plus à chaque changement du PIR :
# on ignore celles qui arrivent moins de 1,5 s après la précédente
# pour garder une fenêtre régulière (30 mesures = 60 s).
MIN_INTERVAL_S = float(os.getenv("MIN_INTERVAL_S", "1.5"))
last_seen = {}

detector = AnomalyDetector()
csv_lock = threading.Lock()
writes = 0


# ------------------------------- données -------------------------------
def trim():
    """Supprime les plus anciennes mesures si le fichier dépasse MAX_ROWS."""
    with open(DATA_PATH, newline="") as f:
        lines = f.readlines()
    if len(lines) - 1 <= MAX_ROWS:
        return
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", newline="") as f:
        f.writelines([lines[0]] + lines[-MAX_ROWS:])
    os.replace(tmp, DATA_PATH)
    print(f"[IA] fichier réduit : {len(lines) - 1} -> {MAX_ROWS} mesures", flush=True)


def record(m):
    """Ajoute une mesure au CSV (sert à l'entraînement)."""
    global writes
    with csv_lock:
        os.makedirs(os.path.dirname(DATA_PATH) or ".", exist_ok=True)
        new = not os.path.exists(DATA_PATH)
        with open(DATA_PATH, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(COLUMNS)
            w.writerow([time.time(), m.get("device_id", "inconnu"), m["temperature"],
                        m["humidity"], m["gas"], m.get("presence", False)])
        writes += 1
        if writes % TRIM_EVERY == 0:
            trim()


def load_series(device_id=None, limit=900):
    """Les `limit` dernières mesures d'un appareil (par défaut : le dernier vu)."""
    if not os.path.exists(DATA_PATH):
        raise ValueError("Aucune mesure enregistrée pour l'instant")
    with csv_lock, open(DATA_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Aucune mesure enregistrée pour l'instant")
    device_id = device_id or rows[-1]["device_id"]
    rows = [r for r in rows if r["device_id"] == device_id][-limit:]
    series = [{"temperature": float(r["temperature"]), "humidity": float(r["humidity"]),
               "gas": float(r["gas"])} for r in rows]
    return series, device_id


def train(device_id=None, limit=900, quantile=0.002):
    series, device_id = load_series(device_id, limit)
    return detector.train(series, device_id, quantile)


# -------------------------------- MQTT --------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[IA] MQTT connecté à {MQTT_HOST}:{MQTT_PORT} ({reason_code})", flush=True)
    client.subscribe(TOPIC_TELEMETRY)


def on_message(client, userdata, msg):
    try:
        m = json.loads(msg.payload.decode())
        dev, now = m.get("device_id", "inconnu"), time.time()
        if now - last_seen.get(dev, 0) < MIN_INTERVAL_S:
            return
        last_seen[dev] = now
        record(m)
        alert = detector.process(m)
        if alert:
            client.publish(TOPIC_ALERTS, json.dumps(alert), qos=1)
            print(f"[IA] alerte {alert['state']} {alert['device_id']} score={alert['score']}", flush=True)
    except Exception as exc:
        print(f"[IA] message ignoré : {exc}", flush=True)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sentinel-anomaly")
client.on_connect = on_connect
client.on_message = on_message


# -------------------------------- API --------------------------------
app = FastAPI(title="Sentinel-X · IA détection d'anomalies")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    def auto_train():
        if detector.model is None:
            try:
                train()
            except Exception as exc:
                print(f"[IA] pas d'entraînement automatique : {exc}", flush=True)

    threading.Thread(target=auto_train, daemon=True).start()


@app.on_event("shutdown")
def shutdown():
    client.loop_stop()
    client.disconnect()


@app.get("/api/anomaly/status")
def status():
    return detector.status()


@app.post("/api/anomaly/train")
async def train_route(device_id: str | None = None, limit: int = 900, quantile: float = 0.002):
    try:
        return await run_in_threadpool(train, device_id, limit, quantile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/health")
def health():
    return {"ok": True, "mqtt": client.is_connected(), "min_samples": MIN_SAMPLES}

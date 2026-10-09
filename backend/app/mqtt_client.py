import asyncio
import json
import os
import threading
import urllib.request
from datetime import timezone

import paho.mqtt.client as mqtt

from app.core.database import SessionLocal
from app.metrics import (
    alerts_total,
    esp8266_status,
    gas_gauge,
    humidity_gauge,
    mqtt_messages_total,
    presence_gauge,
    temperature_gauge,
)
from app.schemas.telemetry import TelemetryCreate
from app.services import websocket as websocket_service
from app.services.alert import alert_from_mqtt, create_alert
from app.services.telemetry import create_telemetry
from app.services.websocket import alerts_manager, manager


# ============================================================================
# CONFIGURATION CAMÉRA
# ============================================================================

# camera.py tourne sur Windows ; le backend tourne dans Docker.
CAMERA_URL = "http://host.docker.internal:9000"

# Une alerte est identifiée par (device_id, source, type).
active_alerts: set[tuple[str, str, str]] = set()
active_alerts_lock = threading.Lock()


# ============================================================================
# CONFIGURATION MQTT
# ============================================================================

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_TELEMETRY = "sentinel/esp8266/telemetry"
TOPIC_EVENTS = "sentinel/esp8266/events"  # PIR / GAS publiés par l'ESP
TOPIC_ALERTS = "sentinel/esp8266/alerts"  # alertes d'anomalie


# ============================================================================
# WEBSOCKET
# ============================================================================

def broadcast(ws_manager, message: dict) -> None:
    """Diffuse un message aux navigateurs depuis le thread MQTT."""
    loop = websocket_service.event_loop
    if loop is None or loop.is_closed():
        print("[WEBSOCKET] Boucle événementielle indisponible ; message non diffusé.")
        return

    try:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(message),
            loop,
        )
    except RuntimeError as exc:
        print(f"[WEBSOCKET] Échec de diffusion : {exc}")


# ============================================================================
# CONNEXION MQTT
# ============================================================================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Appelée lorsque le backend se connecte au broker MQTT."""
    if reason_code == 0:
        print(f"MQTT connecté à {MQTT_BROKER}:{MQTT_PORT}")

        for topic in (TOPIC_TELEMETRY, TOPIC_EVENTS, TOPIC_ALERTS):
            result, _ = client.subscribe(topic)
            print(f"Abonnement demandé à {topic} (result={result})")
    else:
        print(f"Échec connexion MQTT : {reason_code}")


# ============================================================================
# UTILITAIRES MÉTRIQUES
# ============================================================================

def get_first_value(data: dict, *keys):
    """Retourne la première valeur présente parmi plusieurs noms possibles."""
    for key in keys:
        if key in data:
            return data[key]
    return None


def normalize_presence(value):
    """Convertit différentes représentations de présence en 0, 1 ou None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if value != 0 else 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes", "on", "detected"):
            return 1
        if normalized in ("false", "0", "no", "off", "none"):
            return 0
    return None


# ============================================================================
# TRAITEMENT DE LA TÉLÉMÉTRIE
# ============================================================================

def handle_telemetry(payload: dict) -> None:
    """Valide, mesure, stocke et diffuse une télémétrie de l'ESP8266."""
    telemetry = TelemetryCreate(**payload)
    telemetry_data = telemetry.model_dump()

    device_id = str(
        get_first_value(telemetry_data, "device_id", "deviceId")
        or "sentinel-01"
    )
    temperature = get_first_value(telemetry_data, "temperature", "temp")
    humidity = get_first_value(telemetry_data, "humidity", "humidite")
    gas = get_first_value(
        telemetry_data, "gas", "gas_level", "gas_value", "mq2"
    )
    presence = get_first_value(
        telemetry_data, "presence", "presence_detected", "motion"
    )

    # Mise à jour des métriques Prometheus.
    if temperature is not None:
        temperature_gauge.labels(device_id).set(float(temperature))
    if humidity is not None:
        humidity_gauge.labels(device_id).set(float(humidity))
    if gas is not None:
        gas_gauge.labels(device_id).set(float(gas))

    normalized_presence = normalize_presence(presence)
    if normalized_presence is not None:
        presence_gauge.labels(device_id).set(normalized_presence)

    # Une télémétrie reçue indique que le boîtier est actuellement joignable.
    esp8266_status.labels(device_id).set(1)
    mqtt_messages_total.inc()

    db = SessionLocal()
    message = telemetry_data

    try:
        saved = create_telemetry(db, telemetry)
        print(f"Télémétrie enregistrée en base ({device_id})")

        created_at = saved.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        message = {
            **telemetry_data,
            "id": saved.id,
            "created_at": created_at.isoformat(),
        }
    except Exception as exc:
        db.rollback()
        print(f"Erreur lors de l'enregistrement de la télémétrie : {exc}")
        # On diffuse quand même la mesure reçue, même si PostgreSQL échoue.
    finally:
        db.close()

    broadcast(manager, message)


# ============================================================================
# CAMÉRA — CONTRÔLE DE L'ENREGISTREMENT
# ============================================================================

def camera_request(endpoint: str) -> bool:
    """Envoie une requête POST au service caméra exécuté sur Windows."""
    url = f"{CAMERA_URL}{endpoint}"
    try:
        request = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(request, timeout=3) as response:
            body = response.read().decode()
            print(f"[CAMERA] {endpoint} -> {response.status} {body}")
            return True
    except Exception as exc:
        print(f"[CAMERA] Erreur {endpoint} : {exc}")
        return False


def start_camera_recording() -> bool:
    return camera_request("/recording/start")


def stop_camera_recording() -> bool:
    return camera_request("/recording/stop")


# ============================================================================
# TRAITEMENT DES ALERTES
# ============================================================================

def handle_alert(topic: str, payload: dict) -> None:
    """Stocke une alerte, met à jour Prometheus, contrôle la caméra et diffuse."""
    alert = alert_from_mqtt(topic, payload)
    db = SessionLocal()

    try:
        saved = create_alert(db, alert)
        print(
            f"Alerte enregistrée : {alert.type} "
            f"{alert.state} ({alert.source})"
        )

        # Compte les événements d'alerte reçus par type.
        alerts_total.labels(str(alert.type)).inc()

        message = {
            **alert.model_dump(),
            "id": saved.id,
            "created_at": saved.created_at.isoformat(),
        }
    except Exception as exc:
        db.rollback()
        print(f"Erreur lors de l'enregistrement de l'alerte : {exc}")
        return
    finally:
        db.close()

    alert_key = (alert.device_id, alert.source, alert.type)
    should_start_recording = False
    should_stop_recording = False

    with active_alerts_lock:
        if alert.state == "TRIGGERED":
            was_empty = len(active_alerts) == 0
            active_alerts.add(alert_key)
            # Démarre uniquement au passage de 0 à 1 alerte active.
            if was_empty:
                should_start_recording = True

        elif alert.state == "CLEARED":
            had_active_alerts = len(active_alerts) > 0
            active_alerts.discard(alert_key)
            # Arrête uniquement si une alerte active vient de se terminer
            # et qu'il n'en reste aucune.
            if had_active_alerts and len(active_alerts) == 0:
                should_stop_recording = True

    if should_start_recording:
        print("[CAMERA] Première alerte active → démarrage de l'enregistrement")
        start_camera_recording()
    elif should_stop_recording:
        print("[CAMERA] Plus aucune alerte active → arrêt de l'enregistrement")
        stop_camera_recording()

    broadcast(alerts_manager, message)


# ============================================================================
# RÉCEPTION DES MESSAGES MQTT
# ============================================================================

def on_message(client, userdata, message) -> None:
    """Décode et route les messages MQTT vers le traitement approprié."""
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"Payload MQTT invalide sur {message.topic} : {exc}")
        return

    try:
        if message.topic == TOPIC_TELEMETRY:
            handle_telemetry(payload)
        elif message.topic in (TOPIC_EVENTS, TOPIC_ALERTS):
            handle_alert(message.topic, payload)
        else:
            print(f"Topic MQTT non géré : {message.topic}")
    except Exception as exc:
        print(f"Erreur traitement {message.topic} : {exc}")


# ============================================================================
# DÉMARRAGE DU CLIENT MQTT
# ============================================================================

def start_mqtt():
    """Démarre le client MQTT en arrière-plan et retourne le client."""
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="sentinel-backend",
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    # Connexion asynchrone : le backend peut démarrer avant Mosquitto.
    client.connect_async(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client

import asyncio
import json
import os
import threading
import urllib.request

from datetime import timezone

import paho.mqtt.client as mqtt

from app.metrics import (
    temperature_gauge,
    humidity_gauge,
    gas_gauge,
    presence_gauge,
    esp8266_status,
    mqtt_messages_total,
    alerts_total,
)

from app.core.database import SessionLocal
from app.schemas.telemetry import TelemetryCreate
from app.services import websocket as websocket_service
from app.services.alert import alert_from_mqtt, create_alert
from app.services.telemetry import create_telemetry
from app.services.websocket import alerts_manager, manager


# ============================================================================
# CONFIGURATION CAMÉRA
# ============================================================================

# camera.py tourne directement sur Windows.
# Le backend tourne dans Docker, donc on utilise host.docker.internal.
CAMERA_URL = "http://host.docker.internal:9000"

# Alertes actuellement actives.
# Une alerte est identifiée par :
# (device_id, source, type)
active_alerts = set()

active_alerts_lock = threading.Lock()


# ============================================================================
# CONFIGURATION MQTT
# ============================================================================

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_TELEMETRY = "sentinel/esp8266/telemetry"
TOPIC_EVENTS = "sentinel/esp8266/events"   # PIR / GAS publiés par l'ESP
TOPIC_ALERTS = "sentinel/esp8266/alerts"   # ANOMALY publiée par l'IA


# ============================================================================
# WEBSOCKET
# ============================================================================

def broadcast(ws_manager, message: dict):
    """Envoie un message aux navigateurs depuis le thread MQTT."""

    if websocket_service.event_loop is not None:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(message),
            websocket_service.event_loop,
        )


# ============================================================================
# MQTT
# ============================================================================

def on_connect(client, userdata, flags, rc, properties=None):

    if rc == 0:

        print("MQTT connecté")

        for topic in (
            TOPIC_TELEMETRY,
            TOPIC_EVENTS,
            TOPIC_ALERTS,
        ):

        for topic in (
            TOPIC_TELEMETRY,
            TOPIC_EVENTS,
            TOPIC_ALERTS,
        ):
            client.subscribe(topic)

            print(
                f"Abonné à : {topic}"
            )

    else:

        print(
            f"Échec connexion MQTT : {rc}"
        )


# ============================================================================
# TÉLÉMÉTRIE
# ============================================================================

def handle_telemetry(payload: dict):

    telemetry = TelemetryCreate(**payload)

    db = SessionLocal()


    try:

        saved = create_telemetry(
            db,
            telemetry,
        )

        print(
            "Télémétrie enregistrée en base"
        )

        # On diffuse la mesure enregistrée
        # avec son id et sa date.
        message = {
            **telemetry_data,
            "id": saved.id,
            "created_at": (
                saved.created_at
                .replace(tzinfo=timezone.utc)
                .isoformat()
            ),
        }


    except Exception as exc:

        db.rollback()

        print(
            f"Erreur lors de l'enregistrement : {exc}"
        )

        message = payload


    finally:

        db.close()

    broadcast(
        manager,
        message,
    )


# ============================================================================
# CAMÉRA — ENREGISTREMENT
# ============================================================================

def camera_request(endpoint: str):
    """
    Envoie une requête POST à camera.py
    depuis le backend Docker.
    """

    url = f"{CAMERA_URL}{endpoint}"

    try:

        request = urllib.request.Request(
            url,
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=3,
        ) as response:

            body = response.read().decode()

            print(
                f"[CAMERA] {endpoint} -> "
                f"{response.status} {body}"
            )

            return True

    except Exception as exc:

        print(
            f"[CAMERA] Erreur {endpoint} : {exc}"
        )

        return False


def start_camera_recording():

    return camera_request(
        "/recording/start"
    )


def stop_camera_recording():

    return camera_request(
        "/recording/stop"
    )


# ============================================================================
# ALERTES
# ============================================================================

def handle_alert(
    topic: str,
    payload: dict,
):

    # ------------------------------------------------------------
    # Conversion du message MQTT en AlertCreate
    # ------------------------------------------------------------

    alert = alert_from_mqtt(
        topic,
        payload,
    )

    # ------------------------------------------------------------
    # Enregistrement PostgreSQL
    # ------------------------------------------------------------

    db = SessionLocal()


    try:

        saved = create_alert(
            db,
            alert,
        )

        print(
            f"Alerte enregistrée : "
            f"{alert.type} "
            f"{alert.state} "
            f"({alert.source})"
        )

        message = {
            **alert.model_dump(),
            "id": saved.id,
            "created_at": saved.created_at.isoformat(),
        }


    except Exception as exc:

        db.rollback()

        print(
            "Erreur lors de l'enregistrement "
            f"de l'alerte : {exc}"
        )

        return


    finally:

        db.close()

    # ------------------------------------------------------------
    # IDENTIFICATION DE L'ALERTE
    # ------------------------------------------------------------

    alert_key = (
        alert.device_id,
        alert.source,
        alert.type,
    )

    should_start_recording = False
    should_stop_recording = False

    # ------------------------------------------------------------
    # MISE À JOUR DES ALERTES ACTIVES
    # ------------------------------------------------------------

    with active_alerts_lock:

        if alert.state == "TRIGGERED":

            # Avant d'ajouter cette alerte :
            # aucune alerte n'était active.
            was_empty = len(active_alerts) == 0

            active_alerts.add(
                alert_key
            )

            # Passage de :
            # 0 alerte → 1 alerte
            if was_empty:

                should_start_recording = True

        elif alert.state == "CLEARED":

            # L'alerte n'est plus active.
            active_alerts.discard(
                alert_key
            )

            # S'il n'y a plus aucune alerte :
            # arrêt de l'enregistrement.
            if len(active_alerts) == 0:

                should_stop_recording = True

    # ------------------------------------------------------------
    # CONTRÔLE DE LA CAMÉRA
    # ------------------------------------------------------------

    if should_start_recording:

        print(
            "[CAMERA] Première alerte active "
            "→ démarrage de l'enregistrement"
        )

        start_camera_recording()

    elif should_stop_recording:

        print(
            "[CAMERA] Plus aucune alerte active "
            "→ arrêt de l'enregistrement"
        )

        stop_camera_recording()

    # ------------------------------------------------------------
    # WEBSOCKET FRONTEND
    # ------------------------------------------------------------

    broadcast(
        alerts_manager,
        message,
    )


# ============================================================================
# RÉCEPTION MQTT
# ============================================================================

def on_message(
    client,
    userdata,
    message,
):

    try:

        payload = json.loads(
            message.payload.decode()
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):

        print(
            f"Payload MQTT invalide "
            f"sur {message.topic}"
        )

        return

    # --------------------------------------------------------
    # Traitement du message
    # --------------------------------------------------------

    try:


        if message.topic == TOPIC_TELEMETRY:

            handle_telemetry(
                payload
            )

        elif message.topic in (
            TOPIC_EVENTS,
            TOPIC_ALERTS,
        ):

            handle_alert(
                message.topic,
                payload,
            )

        else:

            print(
                f"Topic MQTT non géré : "
                f"{message.topic}"
            )

    except Exception as exc:

        print(
            f"Erreur traitement "
            f"{message.topic} : {exc}"
        )

        print(
            f"Erreur traitement "
            f"{message.topic} : {exc}"
        )


# ============================================================================
# DÉMARRAGE MQTT
# ============================================================================

def start_mqtt():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="sentinel-backend",
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.reconnect_delay_set(
        min_delay=1,
        max_delay=10,
    )

    client.reconnect_delay_set(
        min_delay=1,
        max_delay=10,
    )

    # Connexion en arrière-plan :
    # le backend ne plante pas si Mosquitto démarre après lui
    # et se reconnecte automatiquement en cas de coupure.
    client.connect_async(
        MQTT_BROKER,
        MQTT_PORT,
    )

    client.loop_start()

    return client
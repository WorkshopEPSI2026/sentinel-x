import asyncio
import json
import os
from datetime import timezone

import paho.mqtt.client as mqtt

from app.core.database import SessionLocal
from app.schemas.telemetry import TelemetryCreate
from app.services import websocket as websocket_service
from app.services.alert import alert_from_mqtt, create_alert
from app.services.telemetry import create_telemetry
from app.services.websocket import alerts_manager, manager


MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_TELEMETRY = "sentinel/esp8266/telemetry"
TOPIC_EVENTS = "sentinel/esp8266/events"   # PIR / GAS publiés par l'ESP
TOPIC_ALERTS = "sentinel/esp8266/alerts"   # ANOMALY publiée par l'IA (ai/anomaly)


def broadcast(ws_manager, message: dict):
    """Envoie un message aux navigateurs depuis le thread MQTT."""
    if websocket_service.event_loop is not None:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(message),
            websocket_service.event_loop,
        )


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("MQTT connecté")
        for topic in (TOPIC_TELEMETRY, TOPIC_EVENTS, TOPIC_ALERTS):
            client.subscribe(topic)
            print(f"Abonné à : {topic}")
    else:
        print(f"Échec connexion MQTT : {rc}")


def handle_telemetry(payload: dict):
    telemetry = TelemetryCreate(**payload)
    db = SessionLocal()
    try:
        saved = create_telemetry(db, telemetry)
        print("Télémétrie enregistrée en base")
        # On diffuse la mesure ENREGISTRÉE (avec id et created_at)
        message = {
            **telemetry.model_dump(),
            "id": saved.id,
            "created_at": saved.created_at.replace(tzinfo=timezone.utc).isoformat(),
        }
    except Exception as exc:
        db.rollback()
        print(f"Erreur lors de l'enregistrement : {exc}")
        message = payload
    finally:
        db.close()
    broadcast(manager, message)


def handle_alert(topic: str, payload: dict):
    alert = alert_from_mqtt(topic, payload)
    db = SessionLocal()
    try:
        saved = create_alert(db, alert)
        print(f"Alerte enregistrée : {alert.type} {alert.state} ({alert.source})")
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
    broadcast(alerts_manager, message)


def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Payload MQTT invalide sur {message.topic}")
        return

    try:
        if message.topic == TOPIC_TELEMETRY:
            handle_telemetry(payload)
        else:
            handle_alert(message.topic, payload)
    except Exception as exc:
        print(f"Erreur traitement {message.topic} : {exc}")


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sentinel-backend")

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    # Connexion en arrière-plan : le backend ne plante plus si Mosquitto
    # démarre après lui, et se reconnecte tout seul en cas de coupure.
    client.connect_async(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    return client

import json
import paho.mqtt.client as mqtt
import asyncio

from app.services.websocket import manager
from app.services import websocket as websocket_service

from app.core.database import SessionLocal
from app.schemas.telemetry import TelemetryCreate
from app.services.telemetry import create_telemetry


MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
MQTT_TOPIC = "sentinel/esp8266/telemetry"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connecté")
        client.subscribe(MQTT_TOPIC)
        print(f"Abonné à : {MQTT_TOPIC}")
    else:
        print(f"Échec connexion MQTT : {rc}")


def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())

        print("Nouvelle télémétrie reçue :")
        print(payload)

        # Validation du payload MQTT
        telemetry = TelemetryCreate(**payload)

        # Création d'une session DB dédiée à ce message MQTT
        db = SessionLocal()

        try:
            create_telemetry(db, telemetry)
            print("Télémétrie enregistrée en base")

        except Exception as exc:
            db.rollback()
            print(f"Erreur lors de l'enregistrement : {exc}")

        finally:
            db.close()
            
        # Diffusion aux clients WebSocket
        if websocket_service.event_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(payload),
                websocket_service.event_loop,
            )

    except json.JSONDecodeError:
        print("Payload MQTT invalide")

    except Exception as exc:
        print(f"Erreur traitement télémétrie : {exc}")


def start_mqtt():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)

    client.loop_start()

    return client
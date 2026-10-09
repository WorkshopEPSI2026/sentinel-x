import asyncio
import json
import os
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


# ============================================================
# CONFIGURATION MQTT
# ============================================================

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_TELEMETRY = "sentinel/esp8266/telemetry"
TOPIC_EVENTS = "sentinel/esp8266/events"
TOPIC_ALERTS = "sentinel/esp8266/alerts"


# ============================================================
# WEBSOCKET
# ============================================================

def broadcast(ws_manager, message: dict):
    """
    Envoie un message aux navigateurs depuis le thread MQTT.
    """
    if websocket_service.event_loop is not None:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(message),
            websocket_service.event_loop,
        )


# ============================================================
# CONNEXION MQTT
# ============================================================

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Appelée lorsque le backend se connecte au broker MQTT.
    """

    if rc == 0:
        print("MQTT connecté")

        for topic in (
            TOPIC_TELEMETRY,
            TOPIC_EVENTS,
            TOPIC_ALERTS,
        ):
            client.subscribe(topic)
            print(f"Abonné à : {topic}")

    else:
        print(f"Échec connexion MQTT : {rc}")


# ============================================================
# UTILITAIRE
# ============================================================

def get_first_value(data: dict, *keys):
    """
    Retourne la première valeur trouvée parmi plusieurs clés.

    Cela permet de rester compatible si le nom d'un champ
    change légèrement dans TelemetryCreate.
    """

    for key in keys:
        if key in data:
            return data[key]

    return None


def normalize_presence(value):
    """
    Convertit différentes représentations de présence
    en 0 ou 1 pour Prometheus.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, (int, float)):
        return 1 if value != 0 else 0

    if isinstance(value, str):
        value = value.strip().lower()

        if value in ("true", "1", "yes", "on", "detected"):
            return 1

        if value in ("false", "0", "no", "off", "none"):
            return 0

    return None


# ============================================================
# TRAITEMENT DE LA TÉLÉMÉTRIE
# ============================================================

def handle_telemetry(payload: dict):
    """
    Traite les données de télémétrie envoyées par l'ESP8266.

    Flux :
        ESP8266
            ↓
        Mosquitto
            ↓
        Backend
            ↓
        PostgreSQL
            ↓
        Prometheus
            ↓
        Grafana
    """

    # --------------------------------------------------------
    # Validation du payload avec le schéma existant
    # --------------------------------------------------------

    telemetry = TelemetryCreate(**payload)

    # --------------------------------------------------------
    # Conversion en dictionnaire
    # --------------------------------------------------------

    telemetry_data = telemetry.model_dump()

    # --------------------------------------------------------
    # Identification du boîtier
    # --------------------------------------------------------

    device_id = get_first_value(
        telemetry_data,
        "device_id",
        "deviceId",
    )

    if device_id is None:
        device_id = "sentinel-01"

    device_id = str(device_id)

    # --------------------------------------------------------
    # Récupération des valeurs capteurs
    # --------------------------------------------------------

    temperature = get_first_value(
        telemetry_data,
        "temperature",
        "temp",
    )

    humidity = get_first_value(
        telemetry_data,
        "humidity",
        "humidite",
    )

    gas = get_first_value(
        telemetry_data,
        "gas",
        "gas_level",
        "gas_value",
        "mq2",
    )

    presence = get_first_value(
        telemetry_data,
        "presence",
        "presence_detected",
        "motion",
    )

    # --------------------------------------------------------
    # PROMETHEUS : mise à jour des métriques
    # --------------------------------------------------------

    if temperature is not None:
        temperature_gauge.labels(device_id).set(
            float(temperature)
        )

    if humidity is not None:
        humidity_gauge.labels(device_id).set(
            float(humidity)
        )

    if gas is not None:
        gas_gauge.labels(device_id).set(
            float(gas)
        )

    normalized_presence = normalize_presence(presence)

    if normalized_presence is not None:
        presence_gauge.labels(device_id).set(
            normalized_presence
        )

    # Si on reçoit une télémétrie, l'ESP8266 est considéré
    # comme connecté.
    esp8266_status.labels(device_id).set(1)

    # Un message MQTT valide vient d'être reçu.
    mqtt_messages_total.inc()

    # --------------------------------------------------------
    # ENREGISTREMENT EN BASE DE DONNÉES
    # --------------------------------------------------------

    db = SessionLocal()

    try:
        saved = create_telemetry(db, telemetry)

        print("Télémétrie enregistrée en base")

        # On diffuse la mesure enregistrée
        # avec son id et sa date de création.
        message = {
            **telemetry_data,
            "id": saved.id,
            "created_at": saved.created_at.replace(
                tzinfo=timezone.utc
            ).isoformat(),
        }

    except Exception as exc:
        db.rollback()

        print(
            f"Erreur lors de l'enregistrement : {exc}"
        )

        # En cas d'erreur DB, on continue à diffuser
        # le payload MQTT original.
        message = payload

    finally:
        db.close()

    # --------------------------------------------------------
    # WEBSOCKET
    # --------------------------------------------------------

    broadcast(manager, message)


# ============================================================
# TRAITEMENT DES ALERTES
# ============================================================

def handle_alert(topic: str, payload: dict):
    """
    Traite les alertes reçues depuis MQTT.
    """

    alert = alert_from_mqtt(topic, payload)

    db = SessionLocal()

    try:
        saved = create_alert(db, alert)

        print(
            f"Alerte enregistrée : "
            f"{alert.type} "
            f"{alert.state} "
            f"({alert.source})"
        )

        # ----------------------------------------------------
        # PROMETHEUS
        # ----------------------------------------------------

        alerts_total.labels(
            str(alert.type)
        ).inc()

        message = {
            **alert.model_dump(),
            "id": saved.id,
            "created_at": saved.created_at.isoformat(),
        }

    except Exception as exc:
        db.rollback()

        print(
            f"Erreur lors de l'enregistrement "
            f"de l'alerte : {exc}"
        )

        return

    finally:
        db.close()

    # --------------------------------------------------------
    # WEBSOCKET ALERTES
    # --------------------------------------------------------

    broadcast(alerts_manager, message)


# ============================================================
# RÉCEPTION DES MESSAGES MQTT
# ============================================================

def on_message(client, userdata, message):
    """
    Fonction appelée à chaque réception d'un message MQTT.
    """

    # --------------------------------------------------------
    # Décodage JSON
    # --------------------------------------------------------

    try:
        payload = json.loads(
            message.payload.decode()
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        print(
            f"Payload MQTT invalide sur "
            f"{message.topic}"
        )

        return

    # --------------------------------------------------------
    # Traitement du message
    # --------------------------------------------------------

    try:

        if message.topic == TOPIC_TELEMETRY:

            handle_telemetry(payload)

        else:

            handle_alert(
                message.topic,
                payload,
            )

    except Exception as exc:

        print(
            f"Erreur traitement "
            f"{message.topic} : {exc}"
        )


# ============================================================
# DÉMARRAGE DU CLIENT MQTT
# ============================================================

def start_mqtt():
    """
    Démarre le client MQTT en arrière-plan.
    """

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

    # --------------------------------------------------------
    # Connexion en arrière-plan
    # --------------------------------------------------------

    client.connect_async(
        MQTT_BROKER,
        MQTT_PORT,
    )

    client.loop_start()

    return client
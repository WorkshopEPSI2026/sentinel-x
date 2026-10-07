"""Réglages communs, modifiables par variables d'environnement (ou fichier .env)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER") or None
MQTT_PASS = os.getenv("MQTT_PASS") or None

TOPIC_TELEMETRY = os.getenv("TOPIC_TELEMETRY", "sentinel/esp8266/telemetry")
TOPIC_ALERTS = os.getenv("TOPIC_ALERTS", "sentinel/esp8266/alerts")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
MODEL_PATH = os.path.join(HERE, "models", "isoforest.joblib")

# Anti-fausses alertes : il faut N fenêtres anormales d'affilée pour déclencher
CONSECUTIVE = int(os.getenv("CONSECUTIVE", "3"))

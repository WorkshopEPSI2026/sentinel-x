from prometheus_client import Counter, Gauge


# ============================================================
# MÉTRIQUES SENTINEL-X
# ============================================================

# -------------------------
# MÉTRIQUES DES CAPTEURS
# -------------------------

temperature_gauge = Gauge(
    "sentinel_temperature_celsius",
    "Temperature mesuree par le DHT22",
    ["device"]
)

humidity_gauge = Gauge(
    "sentinel_humidity_percent",
    "Humidite mesuree par le DHT22",
    ["device"]
)

gas_gauge = Gauge(
    "sentinel_gas_level",
    "Niveau de gaz mesure par le MQ-2",
    ["device"]
)

presence_gauge = Gauge(
    "sentinel_presence_detected",
    "Presence detectee par le PIR",
    ["device"]
)


# -------------------------
# ÉTAT DU SYSTÈME
# -------------------------

esp8266_status = Gauge(
    "sentinel_esp8266_status",
    "Etat de connexion de l'ESP8266",
    ["device"]
)


# -------------------------
# MQTT
# -------------------------

mqtt_messages_total = Counter(
    "sentinel_mqtt_messages_received_total",
    "Nombre total de messages MQTT recus"
)


# -------------------------
# ALERTES
# -------------------------

alerts_total = Counter(
    "sentinel_alerts_total",
    "Nombre total d'alertes generees",
    ["type"]
)


# -------------------------
# IA VISION
# -------------------------

ai_detections_total = Counter(
    "sentinel_ai_detections_total",
    "Nombre total de detections realisees par l'IA",
    ["class_name"]
)


# -------------------------
# ANOMALIES
# -------------------------

anomalies_total = Counter(
    "sentinel_anomalies_total",
    "Nombre total d'anomalies detectees"
)
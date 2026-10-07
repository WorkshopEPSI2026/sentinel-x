import paho.mqtt.client as mqtt
from config import MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS


def make_client(client_id: str) -> mqtt.Client:
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if MQTT_USER:
        c.username_pw_set(MQTT_USER, MQTT_PASS)
    # Plus tard (TLS sur 8883) : c.tls_set(ca_certs="chemin/ca.crt")
    c.reconnect_delay_set(min_delay=1, max_delay=10)
    return c

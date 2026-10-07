#!/usr/bin/env python3
"""
Simulateur d'ESP8266 : publie des mesures réalistes sur MQTT, au même format
que le firmware (device_id, temperature, humidity, gas, presence).
Sert à tester sans le boîtier et à générer des données d'entraînement.

    python simulate.py                       # régime normal, 1 mesure / 2 s
    python simulate.py --speed 10            # 10x plus vite (collecte rapide)
    python simulate.py --scenario derive     # 2 min normal puis dérive lente temp + gaz
    python simulate.py --scenario pic        # 2 min normal puis pic de gaz brutal
"""
import argparse
import json
import math
import random
import time

from config import TOPIC_TELEMETRY
from mqtt_utils import make_client


def generate(scenario: str = "normal", warmup: int = 60, seed: int | None = None):
    """Générateur infini de mesures. Utilisé aussi par train.py pour l'évaluation."""
    rnd = random.Random(seed)
    i = 0
    temp_drift = gas_drift = 0.0
    while True:
        # régime normal : petites variations lentes + bruit de capteur
        temp = 23.0 + 0.4 * math.sin(i / 300) + rnd.gauss(0, 0.08)
        hum = 45.0 + 1.0 * math.sin(i / 400) + rnd.gauss(0, 0.3)
        gas = 180 + 6 * math.sin(i / 200) + rnd.gauss(0, 4)

        k = i - warmup
        if scenario == "derive" and k > 0:
            temp_drift += 0.02          # +1 °C toutes les 50 mesures (~100 s)
            gas_drift += 1.6            # le gaz monte doucement
        elif scenario == "pic" and 0 < k < 15:
            gas_drift = 450             # fuite brutale pendant 30 s
        elif scenario == "pic":
            gas_drift = 0

        yield {
            "device_id": "esp8266-sim",
            "temperature": round(temp + temp_drift, 1),
            "humidity": round(hum, 1),
            "gas": int(max(0, min(1023, gas + gas_drift))),
            "presence": rnd.random() < 0.05,
        }
        i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["normal", "derive", "pic"], default="normal")
    ap.add_argument("--speed", type=float, default=1.0, help="accélération (10 = 10x plus vite)")
    ap.add_argument("--warmup", type=int, default=60, help="mesures normales avant l'incident")
    a = ap.parse_args()

    c = make_client("sentinel-simulateur")
    from config import MQTT_HOST, MQTT_PORT
    c.connect(MQTT_HOST, MQTT_PORT)
    c.loop_start()
    print(f"[SIM] scénario {a.scenario} -> {TOPIC_TELEMETRY} (Ctrl+C pour arrêter)")
    for n, m in enumerate(generate(a.scenario, a.warmup)):
        c.publish(TOPIC_TELEMETRY, json.dumps(m))
        if n % 10 == 0:
            print(f"[SIM] #{n} T={m['temperature']} H={m['humidity']} gaz={m['gas']}")
        time.sleep(2.0 / a.speed)


if __name__ == "__main__":
    main()

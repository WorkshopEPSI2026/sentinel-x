#!/usr/bin/env python3
"""
Étape 1 : collecter des mesures NORMALES pour l'entraînement.

Écoute la télémétrie MQTT et l'enregistre dans data/normal.csv.
Laisser tourner au moins 30 min avec le boîtier au calme
(ou ~3 min avec : python simulate.py --speed 10).

    python collect.py --minutes 30
"""
import argparse
import csv
import json
import os
import time

from config import DATA_DIR, MQTT_HOST, MQTT_PORT, TOPIC_TELEMETRY
from features import is_valid
from mqtt_utils import make_client

FIELDS = ["ts", "device_id", "temperature", "humidity", "gas", "presence"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--out", default=os.path.join(DATA_DIR, "normal.csv"))
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    new_file = not os.path.exists(a.out)
    f = open(a.out, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new_file:
        w.writeheader()
    count = {"ok": 0, "rejet": 0}

    def on_message(client, userdata, msg):
        try:
            m = json.loads(msg.payload)
        except json.JSONDecodeError:
            count["rejet"] += 1
            return
        if not is_valid(m):
            count["rejet"] += 1
            return
        w.writerow({"ts": time.time(), **{k: m.get(k) for k in FIELDS[1:]}})
        count["ok"] += 1
        if count["ok"] % 50 == 0:
            f.flush()
            print(f"[COLLECTE] {count['ok']} mesures enregistrées")

    c = make_client("sentinel-ia-collect")
    c.on_connect = lambda cl, u, fl, rc, p: cl.subscribe(TOPIC_TELEMETRY)
    c.on_message = on_message
    c.connect(MQTT_HOST, MQTT_PORT)
    c.loop_start()
    print(f"[COLLECTE] écoute {TOPIC_TELEMETRY} pendant {a.minutes} min -> {a.out}")
    try:
        time.sleep(a.minutes * 60)
    except KeyboardInterrupt:
        pass
    c.loop_stop()
    f.close()
    print(f"[COLLECTE] terminé : {count['ok']} mesures, {count['rejet']} rejetées")


if __name__ == "__main__":
    main()

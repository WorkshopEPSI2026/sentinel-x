"""
Détection d'anomalies — Isolation Forest (service IA autonome).

- Chaque mesure reçue passe dans une FENÊTRE GLISSANTE de 30 mesures (60 s).
- La fenêtre est résumée en 7 caractéristiques : température, humidité, gaz,
  pente température, pente gaz, agitation du gaz, corrélation temp/gaz.
- L'Isolation Forest a appris le comportement NORMAL ; il donne un score
  (plus il est bas, plus c'est anormal).
- 3 fenêtres anormales d'affilée -> ANOMALY TRIGGERED, retour au normal -> CLEARED.
"""
import os
import threading
from collections import deque
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

WINDOW = 30
CONSECUTIVE = int(os.getenv("CONSECUTIVE", "3"))
MIN_SAMPLES = 150
MODEL_PATH = os.getenv("MODEL_PATH", "models/anomaly_model.joblib")

FEATURE_NAMES = ["temp", "hum", "gas", "temp_slope", "gas_slope", "gas_std", "corr_tg"]


# ------------------------------ caractéristiques ------------------------------
def _slope(v):
    return float(np.polyfit(np.arange(len(v)), v, 1)[0])


def _corr(a, b):
    if a.std() < 1e-9 or b.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def compute_features(window):
    t = np.array([m["temperature"] for m in window], dtype=float)
    h = np.array([m["humidity"] for m in window], dtype=float)
    g = np.array([m["gas"] for m in window], dtype=float)
    return [t[-1], h[-1], g[-1], _slope(t), _slope(g), float(g.std()), _corr(t, g)]


def _windows(series):
    return np.array([compute_features(series[i - WINDOW:i]) for i in range(WINDOW, len(series) + 1)])


def _count_alerts(scores, threshold):
    n, streak, active = 0, 0, False
    for s in scores:
        streak = streak + 1 if s < threshold else 0
        if streak >= CONSECUTIVE and not active:
            n, active = n + 1, True
        elif streak == 0:
            active = False
    return n


def _first_alert(scores, threshold):
    streak = 0
    for i, s in enumerate(scores):
        streak = streak + 1 if s < threshold else 0
        if streak >= CONSECUTIVE:
            return i
    return None


def _with_drift(series):
    """Copie de la série avec une dérive lente simulée (temp + gaz)."""
    base = [dict(series[i % len(series)]) for i in range(max(WINDOW + 400, len(series)))]
    for k, m in enumerate(base[WINDOW:]):
        m["temperature"] += 0.02 * k
        m["gas"] = min(1023, m["gas"] + 1.6 * k)
    return base


# ------------------------------- le détecteur -------------------------------
class AnomalyDetector:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.threshold = None
        self.info = {"trained": False}
        self.buffers, self.streak, self.active, self.last_score = {}, {}, {}, {}
        self.load()

    def load(self):
        if not os.path.exists(MODEL_PATH):
            return
        try:
            bundle = joblib.load(MODEL_PATH)
            self.model, self.threshold = bundle["model"], float(bundle["threshold"])
            self.info = {**bundle.get("info", {}), "trained": True}
            print(f"[IA] modèle chargé ({MODEL_PATH})", flush=True)
        except Exception as exc:
            print(f"[IA] modèle illisible, à réentraîner : {exc}", flush=True)

    def train(self, series, device_id, quantile=0.002):
        """series : liste de {temperature, humidity, gas} supposées NORMALES (ordre chronologique)."""
        if len(series) < MIN_SAMPLES:
            raise ValueError(f"Pas assez de mesures pour {device_id} : {len(series)} (minimum {MIN_SAMPLES})")

        cut = int(len(series) * 0.8)
        train, test = series[:cut], series[cut:]
        X = _windows(train)
        model = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(X)
        threshold = float(np.quantile(model.decision_function(X), quantile))

        # Évaluation : fausses alertes sur des données jamais vues + dérive simulée
        s_test = model.decision_function(_windows(test))
        drift = _with_drift(test)
        i = _first_alert(model.decision_function(_windows(drift)), threshold)
        cross = next((j - WINDOW for j, m in enumerate(drift) if j >= WINDOW and m["gas"] >= 600), None)

        info = {
            "trained": True,
            "device_id": device_id,
            "samples": len(series),
            "windows": int(len(X)),
            "threshold": round(threshold, 4),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "eval_false_alerts": _count_alerts(s_test, threshold),
            "eval_drift_detected_after_s": None if i is None else (i - 1) * 2,
            "eval_fixed_threshold_600_after_s": None if cross is None else cross * 2,
        }
        os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
        joblib.dump({"model": model, "threshold": threshold, "window": WINDOW,
                     "features": FEATURE_NAMES, "info": info}, MODEL_PATH)
        with self.lock:
            self.model, self.threshold, self.info = model, threshold, info
            self.buffers.clear(); self.streak.clear(); self.active.clear(); self.last_score.clear()
        print(f"[IA] modèle entraîné : {info}", flush=True)
        return info

    def process(self, m):
        """Ajoute une mesure ; renvoie une alerte (dict) si l'état change, sinon None."""
        dev = m.get("device_id", "inconnu")
        with self.lock:
            if self.model is None:
                return None
            buf = self.buffers.setdefault(dev, deque(maxlen=WINDOW))
            buf.append({"temperature": float(m["temperature"]), "humidity": float(m["humidity"]),
                        "gas": float(m["gas"])})
            if len(buf) < WINDOW:
                return None
            x = compute_features(list(buf))
            score = float(self.model.decision_function([x])[0])
            self.last_score[dev] = round(score, 4)
            self.streak[dev] = self.streak.get(dev, 0) + 1 if score < self.threshold else 0

            if self.streak[dev] >= CONSECUTIVE and not self.active.get(dev):
                self.active[dev] = True
                return {"device_id": dev, "source": "ml", "type": "ANOMALY", "state": "TRIGGERED",
                        "score": round(score, 4),
                        "detail": {k: round(v, 3) for k, v in zip(FEATURE_NAMES, x)}}
            if self.streak[dev] == 0 and self.active.get(dev):
                self.active[dev] = False
                return {"device_id": dev, "source": "ml", "type": "ANOMALY", "state": "CLEARED",
                        "score": round(score, 4), "detail": None}
        return None

    def status(self):
        with self.lock:
            return {**self.info, "model_path": MODEL_PATH, "window": WINDOW, "consecutive": CONSECUTIVE,
                    "devices": {d: {"buffer": len(b), "last_score": self.last_score.get(d),
                                    "in_anomaly": self.active.get(d, False)}
                                for d, b in self.buffers.items()}}

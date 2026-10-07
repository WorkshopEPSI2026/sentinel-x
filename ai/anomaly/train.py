#!/usr/bin/env python3
"""
Étape 2 : entraîner l'Isolation Forest sur les mesures normales, puis l'évaluer.

    python train.py                      # lit data/normal.csv
    python train.py --csv autre.csv

Principe de l'Isolation Forest : le modèle construit des arbres qui coupent les
données au hasard. Un point NORMAL ressemble à beaucoup d'autres : il faut
beaucoup de coupures pour l'isoler. Un point ANORMAL est isolé en très peu de
coupures. Le score est donc bas pour les anomalies.
On n'entraîne QUE sur du normal : pas besoin d'exemples de pannes.

Évaluation (sans matériel) : on garde les 20 % les plus récents des données,
on vérifie qu'ils ne déclenchent pas d'alerte, puis on y AJOUTE artificiellement
une dérive lente (temp + gaz) et un pic de gaz pour mesurer le délai de détection.
"""
import argparse
import csv
import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from config import CONSECUTIVE, DATA_DIR, MODEL_PATH
from features import FEATURE_NAMES, WINDOW, compute_features, is_valid

GAS_ALARM = 600  # seuil "classique" du firmware, pour comparer


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)]
    out = []
    for r in rows:
        m = {"temperature": r["temperature"], "humidity": r["humidity"], "gas": r["gas"]}
        if is_valid(m):
            out.append({k: float(v) for k, v in m.items()})
    return out


def windows(series):
    return np.array([compute_features(series[i - WINDOW:i]) for i in range(WINDOW, len(series) + 1)])


def first_alert(scores, threshold):
    """Indice de la première fenêtre où CONSECUTIVE scores d'affilée sont sous le seuil."""
    streak = 0
    for i, s in enumerate(scores):
        streak = streak + 1 if s < threshold else 0
        if streak >= CONSECUTIVE:
            return i
    return None


def count_alerts(scores, threshold):
    n, streak, active = 0, 0, False
    for s in scores:
        streak = streak + 1 if s < threshold else 0
        if streak >= CONSECUTIVE and not active:
            n, active = n + 1, True
        elif streak == 0:
            active = False
    return n


def inject(series, kind, start=WINDOW):
    """Copie la série en y ajoutant une dérive lente ou un pic de gaz à partir de `start`."""
    need = start + 400
    base = [dict(series[i % len(series)]) for i in range(max(need, len(series)))]
    for k, m in enumerate(base[start:]):
        if kind == "derive":
            m["temperature"] += 0.02 * k
            m["gas"] = min(1023, m["gas"] + 1.6 * k)
        elif kind == "pic" and k < 15:
            m["gas"] = min(1023, m["gas"] + 450)
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(DATA_DIR, "normal.csv"))
    ap.add_argument("--quantile", type=float, default=0.002,
                    help="part des fenêtres normales tolérées sous le seuil (0.002 = 0,2 %%)")
    a = ap.parse_args()

    data = load_csv(a.csv)
    print(f"{len(data)} mesures valides dans {a.csv}")
    if len(data) < 5 * WINDOW:
        raise SystemExit(f"Pas assez de données : il en faut au moins {5 * WINDOW}. Lancez collect.py plus longtemps.")

    cut = int(len(data) * 0.8)
    train, test = data[:cut], data[cut:]
    X = windows(train)
    print(f"Entraînement sur {len(X)} fenêtres de {WINDOW} mesures, {len(FEATURE_NAMES)} caractéristiques")

    model = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(X)
    # Seuil de décision : on le place sous presque tous les scores normaux
    threshold = float(np.quantile(model.decision_function(X), a.quantile))
    print(f"Seuil de décision : {threshold:.4f}  (score < seuil = anormal)")

    # --- Évaluation ---
    print("\n=== Évaluation sur les 20 % de données jamais vues ===")
    s_norm = model.decision_function(windows(test))
    fa = count_alerts(s_norm, threshold)
    print(f"Normal  : {len(s_norm)} fenêtres -> {fa} fausse(s) alerte(s)")

    for kind in ("derive", "pic"):
        serie = inject(test, kind)
        s = model.decision_function(windows(serie))
        i = first_alert(s, threshold)
        start = WINDOW  # début de l'incident (en indice de mesure)
        if i is None:
            print(f"{kind:7s} : NON détecté")
            continue
        idx = i + WINDOW - 1                     # indice de la mesure correspondante
        gas_now = serie[idx]["gas"]
        cross = next((j for j, m in enumerate(serie) if j >= start and m["gas"] >= GAS_ALARM), None)
        msg = f"{kind:7s} : alerte {idx - start} mesures après le début ({(idx - start) * 2} s), gaz = {gas_now:.0f}"
        if kind == "derive" and cross is not None:
            msg += f" ; le seuil fixe {GAS_ALARM} n'aurait sonné qu'à {cross - start} mesures ({(cross - start) * 2} s)"
        print(msg)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": model, "threshold": threshold, "window": WINDOW,
                 "features": FEATURE_NAMES}, MODEL_PATH)
    print(f"\nModèle enregistré : {MODEL_PATH}")


if __name__ == "__main__":
    main()

"""
Calcul des caractéristiques (features) sur une fenêtre glissante de mesures.

Pourquoi une fenêtre ? Une valeur seule (ex. 25 °C) ne dit rien.
Ce qui est anormal, c'est souvent une TENDANCE : la température qui monte
lentement EN MÊME TEMPS que le gaz. On résume donc les N dernières mesures
en quelques nombres que le modèle sait comparer.
"""
import numpy as np

# Taille de la fenêtre : 30 mesures = 60 s si l'ESP envoie toutes les 2 s
WINDOW = 30

FEATURE_NAMES = [
    "temp",        # dernière température
    "hum",         # dernière humidité
    "gas",         # dernière valeur de gaz (brute 0..1023)
    "temp_slope",  # pente de la température (°C par mesure)
    "gas_slope",   # pente du gaz (unités par mesure)
    "gas_std",     # agitation du gaz (écart-type)
    "corr_tg",     # corrélation température / gaz (-1..1)
]


def _slope(values: np.ndarray) -> float:
    """Pente de la droite qui passe au mieux par les points (régression linéaire)."""
    x = np.arange(len(values))
    return float(np.polyfit(x, values, 1)[0])


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    """Corrélation de Pearson ; 0 si une des séries est constante."""
    if a.std() < 1e-9 or b.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def compute_features(window: list[dict]) -> list[float]:
    """window = liste de mesures {temperature, humidity, gas, ...}, la plus récente en dernier."""
    t = np.array([m["temperature"] for m in window], dtype=float)
    h = np.array([m["humidity"] for m in window], dtype=float)
    g = np.array([m["gas"] for m in window], dtype=float)
    return [
        t[-1],
        h[-1],
        g[-1],
        _slope(t),
        _slope(g),
        float(g.std()),
        _corr(t, g),
    ]


def is_valid(m: dict) -> bool:
    """Ignore les mesures incomplètes (DHT22 en erreur, champ manquant...)."""
    try:
        return all(np.isfinite(float(m[k])) for k in ("temperature", "humidity", "gas"))
    except (KeyError, TypeError, ValueError):
        return False

# IA — Détection d'anomalies (Isolation Forest)

Service autonome, à côté de l'IA vision (`ai/app`). Le backend n'est pas modifié :
il reçoit déjà les alertes sur `sentinel/esp8266/alerts`, les enregistre et les pousse au dashboard.

```
ESP8266 --telemetry--> MQTT --> ai/anomaly (fenêtre 60 s + Isolation Forest)
                                   |  alerte ANOMALY TRIGGERED / CLEARED
                                   v
                       MQTT sentinel/esp8266/alerts --> backend --> base + dashboard (WebSocket)
```

| Fichier | Rôle |
|---|---|
| `detector.py` | caractéristiques (7), entraînement, détection en direct |
| `main.py` | abonnement MQTT, enregistrement des mesures, API HTTP |
| `data/telemetry.csv` | mesures reçues (créé automatiquement, sert à l'entraînement) |
| `models/anomaly_model.joblib` | modèle entraîné |

## Lancer

```bash
docker compose up -d --build anomaly
docker logs -f sentinel-anomaly
```

## Entraîner

1. Laisser le boîtier mesurer **au calme** au moins 5 min (150 mesures minimum, idéalement 20-30 min).
2. Bouton **« Entraîner le modèle »** sur le dashboard, ou `POST http://localhost:8002/api/anomaly/train`
   (Swagger : http://localhost:8002/docs).
3. Au démarrage, si aucun modèle n'existe et qu'il y a assez de mesures, l'entraînement se fait tout seul.

## API

| Route | Rôle |
|---|---|
| `GET /api/anomaly/status` | modèle, seuil, évaluation, score en direct par appareil |
| `POST /api/anomaly/train?device_id=&limit=900` | entraîne sur les dernières mesures enregistrées |
| `GET /health` | service et connexion MQTT |

## Comment ça décide

- Fenêtre glissante de 30 mesures (60 s) → 7 caractéristiques : température, humidité, gaz,
  pente température, pente gaz, agitation du gaz, corrélation température/gaz.
- Score Isolation Forest : plus il est bas, plus c'est anormal. Seuil = 0,2 % des scores normaux.
- 3 fenêtres anormales d'affilée → `ANOMALY TRIGGERED` ; retour au normal → `CLEARED`.
- Évaluation automatique à l'entraînement : 0 fausse alerte sur des mesures jamais vues,
  dérive lente détectée en ~12 s contre ~520 s pour un seuil fixe « gaz > 600 ».

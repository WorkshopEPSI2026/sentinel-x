# Détection d'anomalies — Isolation Forest (F-IA-03 / F-IA-04)

Repère un comportement anormal des capteurs **sans seuil fixe** : le modèle apprend
ce qui est « normal », puis signale ce qui ne lui ressemble pas. Il voit en
particulier une **dérive lente** (température et gaz qui montent ensemble) bien
avant l'alarme gaz classique (600).

## Fonctionnement

```
ESP ──MQTT sentinel/esp8266/telemetry──► detect.py
                                           │ fenêtre glissante des 30 dernières mesures (60 s)
                                           │ 7 caractéristiques : temp, hum, gaz, pente temp,
                                           │ pente gaz, agitation du gaz, corrélation temp/gaz
                                           ▼
                                   Isolation Forest → score
                                           │ 3 fenêtres anormales d'affilée
                                           ▼
                   MQTT sentinel/esp8266/alerts  {"type":"ANOMALY","state":"TRIGGERED",...}
```

| Fichier | Rôle |
|---|---|
| `features.py` | Transforme une fenêtre de mesures en caractéristiques |
| `simulate.py` | Faux ESP (scénarios `normal`, `derive`, `pic`) pour tester sans matériel |
| `collect.py` | Étape 1 : enregistre des mesures normales dans `data/normal.csv` |
| `train.py` | Étape 2 : entraîne, choisit le seuil, **évalue** (fausses alertes, délai de détection) |
| `detect.py` | Étape 3 : détection en temps réel, publie les alertes |

## Installation (Windows, une fois)

```powershell
cd ai\anomaly
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Le broker Docker doit tourner (`docker compose up -d mqtt`), port 1883.

## Utilisation

```powershell
# 1. Collecter du normal : 30 min avec le vrai boîtier au calme...
python collect.py --minutes 30
#    ...ou en 3 min avec le simulateur (2 terminaux) :
python simulate.py --speed 10
python collect.py --minutes 3

# 2. Entraîner et évaluer
python train.py

# 3. Détecter en direct
python detect.py
#    test : dans un autre terminal
python simulate.py --scenario derive
```

Exemple de résultat de `train.py` (données simulées) :

```
Normal  : 258 fenêtres -> 0 fausse(s) alerte(s)
derive  : alerte 16 mesures après le début (32 s), gaz = 205 ; le seuil fixe 600 n'aurait sonné qu'à 262 mesures (524 s)
pic     : alerte 2 mesures après le début (4 s), gaz = 627
```

## Réglages

| Réglage | Où | Effet |
|---|---|---|
| `WINDOW` | `features.py` | Taille de la fenêtre (30 = 60 s à 1 mesure / 2 s) |
| `--quantile` | `train.py` | Sensibilité : plus petit = moins de fausses alertes, détection plus tardive |
| `CONSECUTIVE` | `.env` | Nombre de fenêtres anormales d'affilée avant l'alerte |

## À savoir

- **Entraîner sur de vraies mesures** du boîtier, dans les conditions de la démo.
  Un modèle entraîné sur le simulateur verra la vraie salle comme « anormale ».
- Si les conditions changent (autre salle, chauffage), recollecter et réentraîner.
- L'ESP doit envoyer de vraies valeurs : avec des valeurs écrites en dur, le modèle n'apprend rien.
- Quand le backend aura une route d'alertes, mettre `BACKEND_ALERT_URL` dans `.env`.

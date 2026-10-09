# 🛡️ SENTINEL-X

> **L'avant-poste industriel du futur**

SENTINEL-X est une solution de **surveillance cyber-physique Edge** destinée à la protection d'infrastructures industrielles isolées.

Le système combine la collecte de données environnementales par **IoT**, la **détection d'intrusions**, l'analyse vidéo par **intelligence artificielle**, la **détection d'anomalies par machine learning** et une infrastructure locale conteneurisée.

L'objectif est de permettre à un opérateur de **surveiller, analyser et réagir en temps réel** aux événements affectant une infrastructure critique, même dans un environnement disposant d'une connectivité limitée.

---

## 📋 Table des matières

- [Contexte](#-contexte)
- [Objectifs](#-objectifs)
- [Fonctionnalités](#️-fonctionnalités)
- [Architecture](#️-architecture)
- [Stack technique](#-stack-technique)
- [Structure du projet](#-structure-du-projet)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Mise en route de l'ESP8266](#-mise-en-route-de-lesp8266)
- [Services](#-services)
- [Communication](#-communication)
- [Base de données et migrations](#️-base-de-données-et-migrations)
- [Sécurité](#-sécurité)
- [Supervision](#-supervision)
- [FabLab : boîtier et câblage](#-fablab--boîtier-et-câblage)
- [Développement](#-développement)
- [Démonstration](#-démonstration)
- [Équipe](#-équipe)
- [Licence](#-licence)

---

# 🎯 Contexte

Dans le cadre de sa stratégie de sécurisation de ses infrastructures isolées, **AetherCorp** souhaite protéger ses micro-centrales énergétiques contre :

- les intrusions physiques ;
- les attaques informatiques ;
- les risques environnementaux ;
- les défaillances potentielles des équipements.

SENTINEL-X constitue un **système Edge local** capable de collecter les informations provenant du terrain, de les analyser localement et de permettre à un opérateur de réagir rapidement.

Le système est conçu pour fonctionner localement afin de limiter sa dépendance à une infrastructure Cloud.

---

# 🚀 Objectifs

- collecter des données provenant de capteurs IoT ;
- transmettre ces données au serveur local (MQTT) ;
- superviser l'état de l'infrastructure en temps réel ;
- détecter les présences physiques (PIR + caméra) ;
- analyser le flux d'une webcam avec une IA de vision ;
- détecter des anomalies dans les séries temporelles ;
- générer des alertes ;
- permettre l'activation d'actionneurs à distance ;
- centraliser les données ;
- superviser l'infrastructure informatique ;
- appliquer des mesures de cybersécurité ;
- proposer une démonstration physique du système (boîtier FabLab).

---

# ⚙️ Fonctionnalités

## 🌡️ Surveillance environnementale

Le boîtier **ESP8266 (Wemos D1 mini)** collecte les informations de ses capteurs et les envoie toutes les **2 secondes** au serveur local via MQTT (Wi-Fi).

| Composant | Broche | Fonction |
|---|---|---|
| DHT22 | D5 | Température et humidité |
| MQ-2 | A0 | Détection de gaz/fumée |
| PIR (HC-SR501) | D6 | Détection de mouvement |
| OLED SSD1306 (I2C) | D2 (SDA) / D1 (SCL) | Affichage local de l'état |
| LED rouge | D3 | **Alarme gaz locale** : clignote quand le gaz dépasse le seuil |
| LED bleue | D0 | **Présence** détectée, ou commande depuis le dashboard |

L'alarme gaz fonctionne **directement dans le boîtier**, même sans réseau. Le seuil se règle dans `sentinel-iot/src/main.cpp` (`GAS_ALARM_ON` / `GAS_ALARM_OFF`). Elle est désactivée pendant la première minute, le temps que le MQ-2 chauffe.

---

## 👁️ Détection vidéo par IA

Une webcam USB connectée au PC serveur analyse l'environnement.

- **Service caméra** (`camera/`, port 9000) : capture la webcam, diffuse le flux vidéo et enregistre les incidents (`camera/recordings`).
- **IA vision** (`ai/`, port 8001) : YOLOv8n détecte les personnes sur les images.

La vidéo reste traitée localement : seuls les résultats de détection sortent du PC.

```text
Webcam USB
   ↓
Service caméra (OpenCV)  ──image──►  IA vision (YOLOv8)
   ↓                                      │
   ◄──────────── personne détectée ───────┘
   ↓
MQTT  sentinel/esp8266/alerts  (type INTRUSION)
   ↓
Backend FastAPI → base de données → WebSocket
   ↓
Dashboard : « Intrusion (caméra) » dans les alertes en cours
```

L'alerte se termine automatiquement après 10 s sans personne détectée.

---

## 📊 Détection d'anomalies (IA)

Service indépendant `ai/anomaly/` (port 8002), basé sur **Isolation Forest** (scikit-learn).

Plutôt qu'un seuil fixe, l'IA **apprend le comportement normal** du boîtier, puis signale tout écart :

- analyse d'une **fenêtre glissante de 60 s** (30 mesures) ;
- **7 indicateurs** : température, humidité, gaz, pente de la température, pente du gaz, agitation du gaz, corrélation température/gaz ;
- alerte `ANOMALY` après **3 fenêtres anormales d'affilée**, fin d'alerte automatique ;
- alertes **explicables** sur le dashboard (« la température monte vite (+1,5 °C/min) », « température et gaz montent ensemble »…) ;
- entraînement en un clic depuis le dashboard, avec auto-évaluation (fausses alertes, délai de détection).

Sur nos tests : **0 fausse alerte**, et une dérive lente détectée en **~12 s**, contre ~520 s pour un seuil fixe « gaz > 600 ».

Documentation complète : [`ai/anomaly/README.md`](ai/anomaly/README.md) et `ai/anomaly/IA_detection_anomalies_Sentinel-X.pdf`.

---

## 🚨 Alertes

| Type | Source | Déclencheur |
|---|---|---|
| `PIR` | Boîtier | mouvement détecté |
| `GAS` | Boîtier | gaz au-dessus du seuil |
| `INTRUSION` | IA vision | personne détectée par la caméra |
| `ANOMALY` | IA anomalies | comportement inhabituel des capteurs |

Toutes les alertes sont enregistrées en base, poussées en temps réel au dashboard (WebSocket) et visibles dans **Alertes en cours** et dans **Historique des alertes**. Une alerte peut être clôturée par l'opérateur (`POST /api/alerts/{id}/resolve`).

---

## 🔔 Actionneurs

Le firmware écoute les commandes MQTT sur `sentinel/esp8266/cmd` :

```json
{"led": "on"}
```

La LED bleue du boîtier s'allume (ou s'éteint avec `"off"`). Test depuis le PC :

```powershell
docker exec -it sentinel-mqtt mosquitto_pub -t sentinel/esp8266/cmd -m '{\"led\":\"on\"}'
```

> Le bouton de commande dans le dashboard (route backend qui publie sur ce topic) reste à ajouter.

---

## 🎞️ Enregistrements vidéo

Le service caméra enregistre les incidents dans `camera/recordings/` (MP4 H.264). Le backend les expose via `GET /api/recordings` et `GET /api/recordings/{filename}`.

---

# 🏗️ Architecture

SENTINEL-X utilise une architecture **Edge Computing locale**.

```text
┌──────────────────────────────────────────────────────────────────┐
│                     PC SERVEUR (Windows)                         │
│                                                                  │
│  ┌───────────────────── Docker Compose ───────────────────────┐  │
│  │                                                            │  │
│  │  Frontend Vue 3 (5173)        Backend FastAPI (8000)       │  │
│  │  PostgreSQL (5432)            Adminer (8080)               │  │
│  │  MQTT Mosquitto (1883)        IA vision YOLOv8 (8001)      │  │
│  │  IA anomalies (8002)          Prometheus / Grafana / cAdvisor │
│  │                                                            │  │
│  └──────────────▲────────────────────────▲────────────────────┘  │
│                 │ MQTT                   │ HTTP /detect          │
│        Service caméra (9000) ────────────┘                       │
│        hors Docker (accès webcam USB)                            │
│                 ▲                                                │
└─────────────────┼────────────────────────────────────────────────┘
                  │ USB                        ▲
               Webcam                          │ Wi-Fi / MQTT
                                               │
                                  ┌────────────┴────────────┐
                                  │   ESP8266 (D1 mini)     │
                                  │   DHT22 · MQ-2 · PIR    │
                                  │   OLED · LED rouge/bleue│
                                  └─────────────────────────┘
```

> Sous Windows, Docker Desktop ne peut pas accéder aux webcams USB : le service caméra tourne donc directement sur le PC. Le script `start.ps1` le lance automatiquement.

---

# 🧱 Stack technique

## Frontend

- Vue 3
- TypeScript
- Vite
- Tailwind CSS
- Axios
- Chart.js

## Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy + Alembic
- paho-mqtt
- JWT (access + refresh tokens)

## IoT

- ESP8266 (Wemos D1 mini)
- C++ / PlatformIO
- MQTT (PubSubClient)
- Mosquitto

## Base de données

- PostgreSQL 16

## Intelligence artificielle

- Python
- OpenCV
- YOLOv8n (Ultralytics) — vision
- scikit-learn (Isolation Forest) — anomalies

## Infrastructure

- Docker
- Docker Compose
- Windows comme serveur Edge local

## Monitoring

- Prometheus
- Grafana
- cAdvisor

## Administration

- Adminer

## FabLab

- Autodesk Fusion 360
- Impression 3D (Creality) / découpe laser

---

# 📁 Structure du projet

```text
sentinel-x/
│
├── backend/                 # API FastAPI, MQTT, WebSocket, base de données
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/             # migrations de la base
│   └── app/
│       ├── main.py
│       ├── mqtt_client.py
│       ├── models/  schemas/  routers/  services/
│       └── ...
│
├── frontend/                # Dashboard Vue 3
│   ├── Dockerfile
│   └── src/
│       ├── components/      # dashboard/, alerts/, telemetry/
│       ├── composables/     # useTelemetry, useAlerts, useAnomaly, useCamera...
│       ├── views/
│       └── services/
│
├── ai/
│   ├── app/                 # IA vision YOLOv8 (port 8001)
│   ├── dockerfile
│   └── anomaly/             # IA détection d'anomalies (port 8002)
│       ├── detector.py
│       ├── main.py
│       └── README.md
│
├── camera/                  # Service caméra (webcam, flux, enregistrements)
│   ├── camera.py
│   ├── lister_cameras.py
│   └── Dockerfile
│
├── sentinel-iot/            # Firmware ESP8266 (PlatformIO)
│   ├── platformio.ini
│   ├── include/secrets.h    # Wi-Fi + IP du serveur (non commité)
│   └── src/main.cpp
│
├── fablab/                  # Boîtier (Fusion 360, impression 3D, laser) + schéma électrique
│
├── infrastructure/
│   ├── mosquitto/
│   └── prometheus/
│
├── docker-compose.yml
├── start.ps1                # lance tout le projet (Docker + migrations + caméra)
├── .env.example
└── README.md
```

---

# 💻 Prérequis

- Windows 10/11 ;
- Docker Desktop ;
- Git ;
- Python 3.10+ (pour le service caméra) ;
- VS Code + PlatformIO (pour le firmware ESP8266) ;
- une webcam USB ;
- le boîtier ESP8266 monté.

Vérifier Docker :

```bash
docker --version
docker compose version
```

---

# 📦 Installation

Cloner le repository :

```bash
git clone <URL_DU_REPOSITORY>
cd sentinel-x
```

Créer le fichier d'environnement (PowerShell) :

```powershell
Copy-Item .env.example .env
```

Adapter ensuite les variables si nécessaire.

---

# 🔐 Configuration

Le projet utilise un fichier `.env` à la racine (voir `.env.example`) :

```env
POSTGRES_DB=sentinel
POSTGRES_USER=sentinel
POSTGRES_PASSWORD=change-me
POSTGRES_PORT=5432

BACKEND_PORT=8000
MQTT_BROKER=mqtt
MQTT_PORT=1883

JWT_SECRET_KEY=<clé secrète longue et aléatoire>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000

ADMINER_PORT=8080
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Optionnel : caméra dans Docker avec un flux réseau (téléphone...)
# CAMERA_SOURCE=http://192.168.1.20:8080/video
```

### ⚠️ Important

- Le fichier `.env` ne doit **jamais être commité** dans Git (il est dans `.gitignore`).
- Le fichier à partager avec l'équipe est `.env.example`.
- `sentinel-iot/include/secrets.h` (mot de passe Wi-Fi) ne doit pas non plus être commité.

---

# 🐳 Lancement

## Méthode recommandée : une seule commande

Depuis la racine du projet :

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Le script :

1. démarre tous les conteneurs (`docker compose up -d`) ;
2. applique les migrations de la base (`alembic upgrade heads`) ;
3. lance le service caméra sur la **webcam USB** (index 1).

Pour utiliser la webcam intégrée du PC :

```powershell
.\start.ps1 -Camera 0
```

## Commandes Docker utiles

```bash
docker compose up -d --build        # (re)construire et lancer
docker compose ps                   # état des conteneurs
docker compose logs -f backend      # logs du backend
docker compose down                 # arrêter (les données sont conservées)
```

> ⚠️ `docker compose down -v` **supprime la base de données** (volume `postgres_data`).

## Caméra dans Docker (flux réseau)

Si la caméra est un flux réseau (et non une webcam USB), définir `CAMERA_SOURCE` dans `.env`, puis :

```bash
docker compose --profile camera up -d --build
```

## Choisir la webcam

Si l'image ne vient pas de la bonne webcam :

```powershell
cd camera
python lister_cameras.py
```

Le script enregistre une photo par webcam détectée (`webcam_0.jpg`, `webcam_1.jpg`…). Lancer ensuite `start.ps1 -Camera <numéro>`.

---

# 📶 Mise en route de l'ESP8266

1. Trouver l'adresse IP du PC serveur : `ipconfig` → **Adresse IPv4** de la carte Wi-Fi.
2. Créer `sentinel-iot/include/secrets.h` :

```cpp
#define WIFI_SSID  "NomDuWifi"
#define WIFI_PASS  "MotDePasse"
#define MQTT_HOST  "192.168.1.42"   // IP du PC serveur
#define MQTT_PORT  1883
#define MQTT_USER  ""
#define MQTT_PASS  ""
```

3. Autoriser MQTT dans le pare-feu Windows (PowerShell administrateur, une seule fois) :

```powershell
New-NetFirewallRule -DisplayName "MQTT Sentinel-X" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow
```

4. Dans VS Code / PlatformIO : **Upload**, puis **Serial Monitor** (115200 bauds) pour vérifier la connexion Wi-Fi et MQTT.

> L'ESP8266 ne fonctionne qu'en **Wi-Fi 2,4 GHz**. Le PC et l'ESP doivent être sur le même réseau.

Vérifier la réception des messages :

```powershell
docker exec -it sentinel-mqtt mosquitto_sub -t "sentinel/#" -v
```

---

# 🌐 Services

| Service | URL |
|---|---|
| Frontend (dashboard) | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API documentation | http://localhost:8000/docs |
| IA vision | http://localhost:8001 |
| IA anomalies (Swagger) | http://localhost:8002/docs |
| Service caméra | http://localhost:9000 |
| MQTT (Mosquitto) | localhost:1883 |
| Adminer | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| cAdvisor | http://localhost:8081 |

---

# 🔌 Connexion à PostgreSQL avec Adminer

Accéder à http://localhost:8080 :

```text
Système : PostgreSQL
Serveur : postgres
Utilisateur : sentinel
Mot de passe : <POSTGRES_PASSWORD>
Base de données : sentinel
```

⚠️ Depuis un conteneur Docker, le serveur PostgreSQL est accessible avec `postgres`, et non `localhost`.

---

# 📡 Communication

## MQTT

MQTT est le canal de tous les événements terrain.

| Topic | Émetteur | Contenu |
|---|---|---|
| `sentinel/esp8266/telemetry` | ESP8266 | mesures toutes les 2 s |
| `sentinel/esp8266/events` | ESP8266 | événements PIR / GAS |
| `sentinel/esp8266/alerts` | IA anomalies, caméra | alertes ANOMALY / INTRUSION |
| `sentinel/esp8266/cmd` | opérateur | commandes vers le boîtier |
| `sentinel/esp8266/status` | ESP8266 | `online` / `offline` (Last Will) |

Exemple de télémétrie :

```json
{"device_id":"esp8266-01","temperature":23.4,"humidity":45.1,"gas":43,"presence":false}
```

## REST API

FastAPI expose une API REST utilisée par le frontend (authentification, télémétrie, alertes…). Documentation interactive : http://localhost:8000/docs.

## WebSocket

Les WebSockets poussent en temps réel la télémétrie et les alertes vers le dashboard.

```text
ESP8266 / IA / caméra
   ↓
 MQTT
   ↓
FastAPI (base de données)
   ↓
WebSocket
   ↓
Vue (dashboard)
```

---

# 🗄️ Base de données et migrations

Le schéma est géré par **Alembic** (`backend/alembic/versions`).

- **À chaque démarrage** : `alembic upgrade heads` (fait automatiquement par `start.ps1`).

```bash
docker compose exec backend alembic upgrade heads
```

- **Seulement après avoir modifié un modèle** (`backend/app/models`) : créer une nouvelle migration.

```bash
docker compose exec backend alembic revision --autogenerate -m "description du changement"
```

> ⚠️ Ne pas lancer `revision --autogenerate` à chaque démarrage : cela crée des migrations en double.

Les données sont conservées dans le volume Docker `postgres_data` (elles survivent à `build`, `up` et `down`).

---

# 🔐 Sécurité

## Mis en place

- authentification **JWT** (access token + refresh token avec rotation) ;
- mots de passe hachés (Argon2) ;
- secrets hors du code (`.env`, `secrets.h`, non commités) ;
- isolation des services dans un réseau Docker dédié ;
- traitement vidéo **local** : seuls les résultats de détection sortent de la caméra ;
- alarme gaz autonome dans le boîtier (fonctionne sans réseau).

## À renforcer

- authentification MQTT (le broker accepte actuellement les connexions anonymes) et TLS ;
- HTTPS ;
- durcissement du serveur et pare-feu ;
- journalisation et audit réseau (Nmap, Wireshark, Trivy…).

---

# 📈 Supervision

Prometheus collecte les métriques (dont celles des conteneurs via cAdvisor), Grafana les affiche dans des dashboards.

```text
Services / cAdvisor
   │ Metrics
   ▼
Prometheus  (http://localhost:9090)
   │
   ▼
Grafana     (http://localhost:3000)
```

---

# 🧰 FabLab : boîtier et câblage

Le dossier `fablab/` contient :

- le **boîtier** du capteur : modèle Fusion 360 (script de génération), fichiers d'impression 3D (STL) et de découpe laser (SVG) ;
- le **schéma électrique** du boîtier : `fablab/montage_electrique.png` (et `.svg`).

---

# 🧑‍💻 Développement

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Backend

Le backend est exécuté dans Docker avec rechargement automatique (`--reload`).

```bash
docker compose logs -f backend
```

Documentation Swagger : http://localhost:8000/docs

## IA anomalies

```bash
docker compose up -d --build anomaly
docker compose logs -f anomaly
```

Entraînement : bouton **« Entraîner le modèle »** sur le dashboard (boîtier au calme pendant au moins 30 min), ou `POST http://localhost:8002/api/anomaly/train`.

## Firmware ESP8266

Ouvrir `sentinel-iot/` dans VS Code avec PlatformIO, puis **Upload**.

---

# 🧪 Tests

Les tests ont été réalisés manuellement de bout en bout (boîtier → MQTT → backend → dashboard).

L'IA anomalies s'auto-évalue à chaque entraînement (fausses alertes sur des données jamais vues, délai de détection d'une dérive simulée).

Des tests automatisés backend (`pytest`) restent à écrire.

---

# 🎥 Démonstration

La démonstration finale reproduit un scénario d'incident sur une infrastructure industrielle.

### 1. État normal

Les capteurs transmettent leurs données toutes les 2 s, et la carte IA affiche « Comportement normal ».

```text
Température : normale
Humidité    : normale
Gaz         : normal
Présence    : aucune
```

### 2. Détection d'une présence

Le capteur PIR détecte un mouvement : la LED bleue s'allume et une alerte « Mouvement (PIR) » apparaît.

```text
PIR → ESP8266 → MQTT → Backend → Alerte
```

### 3. Détection vidéo

La webcam détecte une personne : alerte « Intrusion (caméra) ».

```text
Webcam → YOLO → personne détectée → MQTT → Backend → Alerte
```

### 4. Anomalie

On chauffe le DHT22 avec la main (ou on approche du gaz du MQ-2) : l'IA détecte un comportement inhabituel avant tout seuil fixe, et affiche l'explication (« la température monte vite… »).

### 5. Alarme gaz

Si le gaz dépasse le seuil, la LED rouge du boîtier clignote, même sans réseau.

### 6. Réaction de l'opérateur

L'opérateur clôture les alertes depuis le dashboard et peut commander la LED du boîtier via MQTT.

```text
Commande → MQTT (sentinel/esp8266/cmd) → ESP8266 → LED
```

### 7. Retour à la normale

Les alertes passent en « FIN » automatiquement quand la situation redevient normale.

---

# 🏆 Objectif du projet

SENTINEL-X vise à démontrer qu'une infrastructure industrielle isolée peut disposer d'une solution de sécurité :

- **locale** ;
- **résiliente** ;
- **intelligente** ;
- **sécurisée** ;
- **observable** ;
- **capable de réagir en temps réel**.

L'approche Edge permet de conserver les traitements critiques localement, sans dépendre d'un service Cloud.

---

# 👥 Équipe

Projet réalisé dans le cadre du workshop **EPSI M1 DEV** — Groupe 1.

**Projet : SENTINEL-X**

> Mission : construire l'avant-poste industriel du futur.

| Membre | Rôle |
|---|---|
| _à compléter_ | _à compléter_ |

---

# 📄 Licence

Projet réalisé dans le cadre pédagogique de l'EPSI.

Usage académique et démonstratif.

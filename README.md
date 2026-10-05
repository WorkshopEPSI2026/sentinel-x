# 🛡️ SENTINEL-X

> **L'avant-poste industriel du futur**

SENTINEL-X est une solution de **surveillance cyber-physique Edge** destinée à la protection d'infrastructures industrielles isolées.

Le système combine la collecte de données environnementales par **IoT**, la **détection d'intrusions**, l'analyse vidéo par **intelligence artificielle**, la détection d'anomalies et une infrastructure locale conteneurisée.

L'objectif est de permettre à un opérateur de **surveiller, analyser et réagir en temps réel** aux événements affectant une infrastructure critique, même dans un environnement disposant d'une connectivité limitée.

---

## 📋 Table des matières

- [Contexte](#-contexte)
- [Objectifs](#-objectifs)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Stack technique](#-stack-technique)
- [Structure du projet](#-structure-du-projet)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Services](#-services)
- [Communication](#-communication)
- [Sécurité](#-sécurité)
- [Supervision](#-supervision)
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

Les objectifs principaux du projet sont :

- collecter des données provenant de capteurs IoT ;
- transmettre ces données de manière sécurisée ;
- superviser l'état de l'infrastructure en temps réel ;
- détecter les présences physiques ;
- analyser le flux d'une webcam avec une IA de vision ;
- détecter des anomalies dans les séries temporelles ;
- générer des alertes ;
- permettre l'activation d'actionneurs à distance ;
- centraliser les données ;
- superviser l'infrastructure informatique ;
- appliquer des mesures de cybersécurité ;
- proposer une démonstration physique du système.

---

# ⚙️ Fonctionnalités

## 🌡️ Surveillance environnementale

L'ESP8266 collecte les informations provenant de différents capteurs :

| Capteur | Fonction |
|---|---|
| DHT22 | Température et humidité |
| MQ-2 | Détection de gaz/fumée |
| PIR | Détection de mouvement |
| OLED | Affichage local |
| Buzzer | Alerte sonore |
| LED | Signalisation visuelle |

Les données sont transmises au serveur local via MQTT.

---

## 👁️ Détection vidéo par IA

Une webcam USB connectée au PC serveur local permet d'analyser l'environnement.

Le module de vision utilise :

- Python ;
- OpenCV ;
- YOLOv8-tiny.

La vidéo reste traitée localement.

Le système transmet uniquement les résultats de détection au backend.

```text
Webcam
   ↓
OpenCV / YOLO
   ↓
Détection d'une personne
   ↓
Backend FastAPI
   ↓
Création d'une alerte
   ↓
Dashboard
```

---

## 📊 Détection d'anomalies

SENTINEL-X prévoit également l'analyse des séries temporelles afin d'identifier des comportements inhabituels.

L'objectif n'est pas simplement d'utiliser des seuils fixes, mais de détecter des comportements anormaux dans les données.

Les algorithmes envisagés comprennent notamment :

- Isolation Forest ;
- Random Forest.

---

## 🚨 Alertes

Les différents événements détectés peuvent générer des alertes :

- mouvement détecté ;
- présence humaine détectée par IA ;
- anomalie environnementale ;
- comportement inhabituel d'un capteur ;
- événement de sécurité.

Les alertes sont ensuite visibles depuis l'interface de supervision.

---

## 🔔 Actionneurs

L'opérateur peut également agir sur le système.

Le backend peut transmettre une commande MQTT à l'ESP8266 afin de :

- allumer une LED ;
- activer le buzzer ;
- signaler une situation d'urgence.

---

# 🏗️ Architecture

SENTINEL-X utilise une architecture **Edge Computing locale**.

```text
                         ┌──────────────────────────┐
                         │       PC SERVEUR         │
                         │        WINDOWS           │
                         │                          │
                         │  ┌────────────────────┐  │
                         │  │ Docker Compose     │  │
                         │  │                    │  │
                         │  │ Vue 3 / Vite       │  │
                         │  │ FastAPI             │  │
                         │  │ PostgreSQL          │  │
                         │  │ MQTT Mosquitto      │  │
                         │  │ Prometheus          │  │
                         │  │ Grafana             │  │
                         │  └────────────────────┘  │
                         │                          │
                         │      Python / YOLO       │
                         │             ▲            │
                         └─────────────┼────────────┘
                                       │
                                    Webcam
                                       │
                              ┌────────▼────────┐
                              │     ESP8266      │
                              │                  │
                              │ DHT22            │
                              │ MQ-2             │
                              │ PIR              │
                              │ OLED             │
                              │ LED              │
                              │ Buzzer           │
                              └──────────────────┘
```

---

# 🧱 Stack technique

## Frontend

- Vue 3
- TypeScript
- Vite
- Tailwind CSS
- Axios

## Backend

- Python
- FastAPI
- Uvicorn

## IoT

- ESP8266
- C++
- MQTT
- Mosquitto

## Base de données

- PostgreSQL

## Intelligence artificielle

- Python
- OpenCV
- YOLOv8-tiny
- scikit-learn

## Infrastructure

- Docker
- Docker Compose
- Windows comme serveur Edge local

## Monitoring

- Prometheus
- Grafana

## Administration

- Adminer

---

# 📁 Structure du projet

```text
sentinel-x/
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── components/
│       ├── views/
│       ├── services/
│       │   └── api.ts
│       └── ...
│
├── infrastructure/
│   ├── mosquitto/
│   │   ├── config/
│   │   └── data/
│   │
│   └── prometheus/
│       └── prometheus.yml
│
├── ai/
│   └── ...
│
├── iot/
│   └── ...
│
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

# 💻 Prérequis

Pour lancer le projet, vous devez disposer de :

- Windows 10/11 ;
- Docker Desktop ;
- Docker Compose ;
- Git ;
- une webcam USB pour la partie vision ;
- un ESP8266 pour la partie IoT.

Vérifier Docker :

```bash
docker --version
```

Puis :

```bash
docker compose version
```

---

# 📦 Installation

Cloner le repository :

```bash
git clone <URL_DU_REPOSITORY>
cd sentinel-x
```

Créer le fichier d'environnement :

```bash
cp .env.example .env
```

Sous PowerShell :

```powershell
Copy-Item .env.example .env
```

Adapter ensuite les variables d'environnement si nécessaire.

---

# 🔐 Configuration

Le projet utilise un fichier `.env` à la racine.

Exemple :

```env
POSTGRES_DB=sentinel
POSTGRES_USER=sentinel
POSTGRES_PASSWORD=change-me
POSTGRES_PORT=5432

BACKEND_PORT=8000

MQTT_BROKER=mqtt
MQTT_PORT=1883

FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000

ADMINER_PORT=8080

PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### ⚠️ Important

Le fichier `.env` ne doit **jamais être commité** dans Git.

Utiliser :

```text
.env
```

dans `.gitignore`.

Le fichier à partager avec l'équipe est :

```text
.env.example
```

---

# 🐳 Lancement avec Docker

Depuis la racine du projet :

```bash
docker compose up --build
```

Pour lancer les conteneurs en arrière-plan :

```bash
docker compose up --build -d
```

Vérifier les conteneurs :

```bash
docker compose ps
```

Arrêter les services :

```bash
docker compose down
```

Voir les logs :

```bash
docker compose logs -f
```

Voir les logs du backend :

```bash
docker compose logs -f backend
```

Voir les logs du frontend :

```bash
docker compose logs -f frontend
```

---

# 🌐 Services

Une fois Docker lancé :

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API documentation | http://localhost:8000/docs |
| Adminer | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

# 🔌 Connexion à PostgreSQL avec Adminer

Accéder à :

```text
http://localhost:8080
```

Utiliser :

```text
Système : PostgreSQL
Serveur : postgres
Utilisateur : sentinel
Mot de passe : <POSTGRES_PASSWORD>
Base de données : sentinel
```

⚠️ Depuis un conteneur Docker, le serveur PostgreSQL est accessible avec :

```text
postgres
```

et non :

```text
localhost
```

---

# 📡 Communication

SENTINEL-X utilise plusieurs mécanismes de communication selon les besoins.

## MQTT

MQTT est utilisé pour les communications IoT.

```text
ESP8266
   │
   │ MQTT
   ▼
Mosquitto
   │
   ▼
FastAPI
```

Il permet notamment de transmettre :

- température ;
- humidité ;
- gaz/fumée ;
- présence ;
- commandes des actionneurs.

---

## REST API

FastAPI expose une API REST utilisée par le frontend.

```text
Vue
 │
 │ HTTP
 ▼
FastAPI
 │
 ├── PostgreSQL
 └── MQTT
```

---

## WebSocket

Les WebSockets sont utilisés pour la remontée des événements en temps réel vers le dashboard.

```text
ESP8266
   ↓
 MQTT
   ↓
FastAPI
   ↓
WebSocket
   ↓
Vue
```

---

# 🔐 Sécurité

La sécurité constitue un des piliers du projet.

Les mesures prévues comprennent notamment :

- isolation des services Docker ;
- segmentation réseau ;
- authentification ;
- communication sécurisée ;
- sécurisation de MQTT ;
- HTTPS ;
- durcissement du serveur ;
- pare-feu ;
- accès SSH par clés ;
- journalisation ;
- supervision ;
- audit réseau.

Les outils envisagés pour les audits comprennent notamment :

- Nmap ;
- Wireshark ;
- Metasploit ;
- Trivy.

---

# 📈 Supervision

Prometheus collecte les métriques exposées par les services.

Grafana permet ensuite de construire des dashboards de supervision.

```text
Services
   │
   │ Metrics
   ▼
Prometheus
   │
   ▼
Grafana
```

Prometheus est accessible à :

```text
http://localhost:9090
```

Grafana :

```text
http://localhost:3000
```

---

# 🧑‍💻 Développement

## Frontend

Entrer dans le dossier :

```bash
cd frontend
```

Installer les dépendances :

```bash
npm install
```

Lancer Vite :

```bash
npm run dev
```

---

## Backend

Le backend est exécuté dans Docker.

Pour suivre ses logs :

```bash
docker compose logs -f backend
```

L'API FastAPI est accessible sur :

```text
http://localhost:8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

---

# 🧪 Tests

Les tests backend sont prévus avec :

```text
pytest
```

Lancer les tests :

```bash
pytest
```

---

# 🎥 Démonstration

La démonstration finale reproduit un scénario d'incident sur une infrastructure industrielle.

### 1. État normal

Les capteurs transmettent leurs données.

```text
Température : normale
Humidité    : normale
Gaz         : normal
Présence    : aucune
```

### 2. Détection d'une présence

Le capteur PIR détecte un mouvement.

```text
PIR
 ↓
ESP8266
 ↓
MQTT
 ↓
Backend
 ↓
Alerte
```

### 3. Détection vidéo

La webcam détecte une présence humaine.

```text
Webcam
 ↓
YOLO
 ↓
Person detected
 ↓
Backend
 ↓
Alerte
```

### 4. Anomalie

Le système détecte un comportement inhabituel dans les données.

### 5. Réaction de l'opérateur

L'opérateur déclenche l'alarme depuis le dashboard.

```text
Dashboard
    ↓
FastAPI
    ↓
MQTT
    ↓
ESP8266
    ↓
LED + Buzzer
```

### 6. Retour à la normale

L'opérateur constate la résolution de l'incident et supervise le retour à l'état normal.

---

# 🏆 Objectif du projet

SENTINEL-X vise à démontrer qu'une infrastructure industrielle isolée peut disposer d'une solution de sécurité :

- **locale** ;
- **résiliente** ;
- **intelligente** ;
- **sécurisée** ;
- **observable** ;
- **capable de réagir en temps réel**.

L'approche Edge permet notamment de conserver les traitements critiques localement, sans dépendre systématiquement d'un service Cloud.

---

# 👥 Équipe

Projet réalisé dans le cadre du workshop **EPSI BAC+4**.

**Projet : SENTINEL-X**

> Mission : construire l'avant-poste industriel du futur.

---

# 📄 Licence

Projet réalisé dans le cadre pédagogique de l'EPSI.

Usage académique et démonstratif.

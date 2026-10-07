// Copier ce fichier en "secrets.h" (même dossier) et le remplir.
// secrets.h est ignoré par Git : les mots de passe ne partent pas sur GitHub.
#pragma once

// Réseau Wi-Fi 2,4 GHz sur lequel est AUSSI connecté le PC serveur
#define WIFI_SSID   "SENTINEL-DORA"
#define WIFI_PASS   "mot-de-passe-du-wifi"

// Adresse IP du PC qui fait tourner Docker (ipconfig sur le PC)
//   hotspot Windows  -> 192.168.137.1
//   hotspot iPhone   -> l'IP du PC sur ce réseau (ex. 172.20.10.4)
#define MQTT_HOST   "192.168.137.1"
#define MQTT_PORT   1883

// Vide tant que Mosquitto accepte les connexions anonymes
#define MQTT_USER   ""
#define MQTT_PASS   ""

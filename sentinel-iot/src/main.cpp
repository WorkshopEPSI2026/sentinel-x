// =====================================================================
//  SENTINEL-X — Firmware ESP8266 (Wemos D1 mini) — groupe 1
//
//  Câblage (voir le guide de branchement) :
//    OLED   SDA -> D2   SCL -> D1   VCC -> 3V3
//    DHT22  DATA -> D5             VCC -> 3V3
//    PIR    OUT -> D6              VCC -> 5V
//    Buzzer I/O -> D7              VCC -> 3V3
//    MQ-2   AO -> A0               VCC -> 5V
//    LED d'alerte = LED bleue de la carte (D4, allumée à LOW)
//
//  MQTT (même format que le backend : app/schemas/telemetry.py)
//    publie   sentinel/esp8266/telemetry  toutes les 2 s + à chaque changement du PIR
//             {"device_id","temperature","humidity","gas","presence"}
//    publie   sentinel/esp8266/events     {"device_id","type":"PIR|GAS","state":"TRIGGERED|CLEARED","value"}
//    publie   sentinel/esp8266/status     "online" / "offline" (Last Will, retenu)
//    écoute   sentinel/esp8266/cmd        {"buzzer":"on"} {"buzzer":"off"} {"led":"on"} {"led":"off"}
//
//  Aucun delay() bloquant dans loop() : tout est cadencé avec millis().
// =====================================================================
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#include "secrets.h"   // WIFI_SSID, WIFI_PASS, MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS

// ---------- Identité et topics ----------
#define DEVICE_ID       "esp8266-01"
#define TOPIC_TELEMETRY "sentinel/esp8266/telemetry"
#define TOPIC_EVENTS    "sentinel/esp8266/events"
#define TOPIC_STATUS    "sentinel/esp8266/status"
#define TOPIC_CMD       "sentinel/esp8266/cmd"

// ---------- Broches ----------
#define PIN_DHT     D5
#define PIN_PIR     D6
#define PIN_BUZZER  D7
#define PIN_GAS     A0
#define PIN_LED     D4          // LED bleue de la carte
#define LED_ON      LOW         // elle s'allume à LOW
#define LED_OFF     HIGH
// Module buzzer : la plupart s'activent à HIGH. Si le vôtre sonne en permanence
// et se tait quand il devrait sonner, inverser ces deux lignes.
#define BUZZER_ON   HIGH
#define BUZZER_OFF  LOW

// ---------- Réglages ----------
#define TELEMETRY_MS    2000    // une mesure toutes les 2 s (le DHT22 ne va pas plus vite)
#define OLED_MS         500
#define RECONNECT_MS    5000
#define GAS_ALARM_ON    600     // alarme locale de sécurité (hystérésis)
#define GAS_ALARM_OFF   520
#define MQ2_WARMUP_MS   60000   // le MQ-2 chauffe ~1 min avant d'être fiable

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
DHT dht(PIN_DHT, DHT22);
WiFiClient net;
PubSubClient mqtt(net);

bool  oledOk = false;
float lastTemp = NAN, lastHum = NAN;   // dernière lecture DHT valide
int   lastGas = 0;
bool  presence = false;
bool  gasAlarm = false;
bool  cmdBuzzer = false, cmdLed = false;   // états demandés par le dashboard
uint32_t tTele = 0, tOled = 0, tReconnect = 0;
uint32_t dhtErrors = 0;

// ---------------------------------------------------------------------
void applyOutputs() {
  // Sortie = commande du dashboard OU alarme gaz locale
  digitalWrite(PIN_BUZZER, (cmdBuzzer || gasAlarm) ? BUZZER_ON : BUZZER_OFF);
  digitalWrite(PIN_LED, (cmdLed || gasAlarm || presence) ? LED_ON : LED_OFF);
}

void publishEvent(const char* type, const char* state, int value) {
  char buf[160];
  snprintf(buf, sizeof(buf),
           "{\"device_id\":\"%s\",\"type\":\"%s\",\"state\":\"%s\",\"value\":%d}",
           DEVICE_ID, type, state, value);
  if (mqtt.connected()) mqtt.publish(TOPIC_EVENTS, buf);
  Serial.printf("[EVENT] %s\n", buf);
}

void publishTelemetry() {
  if (isnan(lastTemp) || isnan(lastHum)) {
    // Jamais de "nan" dans le JSON : le backend rejetterait le message
    Serial.println("[TELE] pas encore de lecture DHT22 valide, envoi reporté");
    return;
  }
  char buf[200];
  snprintf(buf, sizeof(buf),
           "{\"device_id\":\"%s\",\"temperature\":%.1f,\"humidity\":%.1f,\"gas\":%d,\"presence\":%s}",
           DEVICE_ID, lastTemp, lastHum, lastGas, presence ? "true" : "false");
  bool ok = mqtt.connected() && mqtt.publish(TOPIC_TELEMETRY, buf);
  Serial.printf("[TELE] %s %s\n", ok ? "->" : "(non envoyé)", buf);
}

// ---------------------------------------------------------------------
void onCommand(char* topic, byte* payload, unsigned int len) {
  char msg[96];
  len = min(len, (unsigned int)sizeof(msg) - 1);
  memcpy(msg, payload, len);
  msg[len] = '\0';
  Serial.printf("[CMD] %s\n", msg);

  // Analyse simple : {"buzzer":"on"} / {"led":"off"} (espaces tolérés)
  bool on = strstr(msg, "\"on\"") || strstr(msg, "true");
  if (strstr(msg, "buzzer")) cmdBuzzer = on;
  if (strstr(msg, "led"))    cmdLed = on;
  applyOutputs();
}

// ---------------------------------------------------------------------
// Explication lisible de l'état Wi-Fi (affichée dans le moniteur série et sur l'OLED)
const char* wifiReason() {
  switch (WiFi.status()) {
    case WL_CONNECTED:       return "connecte";
    case WL_NO_SSID_AVAIL:   return "RESEAU INTROUVABLE (nom faux, 5 GHz ou trop loin)";
    case WL_WRONG_PASSWORD:  return "MOT DE PASSE FAUX";
    case WL_CONNECT_FAILED:  return "ECHEC (mot de passe ?)";
    case WL_CONNECTION_LOST: return "connexion perdue";
    case WL_DISCONNECTED:    return "en cours / deconnecte";
    default:                 return "en attente";
  }
}

// Au démarrage : liste des réseaux 2,4 GHz que l'ESP voit (il ne voit jamais le 5 GHz)
void scanNetworks() {
  Serial.println("[WIFI] Recherche des reseaux visibles...");
  int n = WiFi.scanNetworks();
  bool found = false;
  for (int i = 0; i < n; i++) {
    bool same = WiFi.SSID(i) == WIFI_SSID;
    found |= same;
    Serial.printf("  %s \"%s\"  signal %d dBm  canal %d%s\n", same ? "=>" : "  ",
                  WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i),
                  WiFi.encryptionType(i) == ENC_TYPE_NONE ? "  (ouvert)" : "");
  }
  if (n <= 0) Serial.println("  aucun reseau visible !");
  Serial.printf("[WIFI] \"%s\" %s\n", WIFI_SSID,
                found ? "TROUVE : si la connexion echoue, c'est le mot de passe"
                      : "ABSENT de la liste : verifier le nom exact et la bande 2,4 GHz");
  WiFi.scanDelete();
}

// ---------------------------------------------------------------------
void connectNetwork() {
  if (WiFi.status() != WL_CONNECTED) {
    // WiFi.begin() est déjà lancé dans setup() ; l'ESP se reconnecte tout seul
    Serial.printf("[WIFI] connexion a \"%s\"... etat : %s\n", WIFI_SSID, wifiReason());
    return;
  }
  if (mqtt.connected()) return;

  Serial.printf("[WIFI] connecte, IP de l'ESP : %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("[MQTT] connexion a %s:%d... ", MQTT_HOST, MQTT_PORT);
  const char* user = strlen(MQTT_USER) ? MQTT_USER : nullptr;
  const char* pass = strlen(MQTT_PASS) ? MQTT_PASS : nullptr;
  // Last Will : si l'ESP disparaît, le broker publie "offline" à sa place
  if (mqtt.connect(DEVICE_ID, user, pass, TOPIC_STATUS, 1, true, "offline")) {
    Serial.println("OK");
    mqtt.publish(TOPIC_STATUS, "online", true);
    mqtt.subscribe(TOPIC_CMD, 1);
  } else {
    Serial.printf("ECHEC rc=%d (-2 = PC injoignable : IP, pare-feu, Docker)\n", mqtt.state());
  }
}

// ---------------------------------------------------------------------
void readSensors() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (!isnan(t) && !isnan(h)) {
    lastTemp = t;
    lastHum = h;
  } else {
    dhtErrors++;
    Serial.printf("[DHT] erreur de lecture (%lu) : on garde la derniere valeur\n", (unsigned long)dhtErrors);
  }

  lastGas = analogRead(PIN_GAS);

  // Alarme gaz locale (fonctionne même sans serveur), ignorée pendant la chauffe
  if (millis() > MQ2_WARMUP_MS) {
    if (!gasAlarm && lastGas >= GAS_ALARM_ON) {
      gasAlarm = true;
      publishEvent("GAS", "TRIGGERED", lastGas);
    } else if (gasAlarm && lastGas <= GAS_ALARM_OFF) {
      gasAlarm = false;
      publishEvent("GAS", "CLEARED", lastGas);
    }
  }
  applyOutputs();
}

void checkPir() {
  bool p = digitalRead(PIN_PIR) == HIGH;
  if (p == presence) return;
  presence = p;
  publishEvent("PIR", p ? "TRIGGERED" : "CLEARED", p ? 1 : 0);
  applyOutputs();
  publishTelemetry();          // le dashboard voit le changement tout de suite
}

void drawOled() {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(0, 0);
  if (WiFi.status() == WL_CONNECTED) oled.print(WiFi.localIP());
  else if (WiFi.status() == WL_NO_SSID_AVAIL) oled.print("WiFi introuvable");
  else if (WiFi.status() == WL_WRONG_PASSWORD) oled.print("WiFi mdp faux");
  else oled.print("WiFi...");
  oled.setCursor(98, 0);
  oled.print(mqtt.connected() ? "MQTT" : "----");
  oled.drawLine(0, 10, 127, 10, SSD1306_WHITE);

  oled.setTextSize(2);
  oled.setCursor(0, 14);
  if (isnan(lastTemp)) oled.print("--.- C");
  else oled.printf("%.1f C", lastTemp);
  oled.setTextSize(1);
  oled.setCursor(84, 14);
  if (!isnan(lastHum)) oled.printf("%.0f %%", lastHum);

  oled.setCursor(0, 34);
  oled.printf("Gaz %4d%s", lastGas, millis() < MQ2_WARMUP_MS ? " chauffe" : "");
  oled.setCursor(0, 44);
  oled.printf("PIR %s", presence ? "MOUVEMENT" : "rien");

  oled.setCursor(0, 56);
  if (gasAlarm)        oled.print("!! ALERTE GAZ !!");
  else if (presence)   oled.print("! PRESENCE !");
  else                 oled.print("Etat : OK");
  oled.display();
}

// ---------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== SENTINEL-X IoT ===");

  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  applyOutputs();

  Wire.begin(D2, D1);
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  Serial.println(oledOk ? "[OLED] OK" : "[OLED] absent (adresse 0x3C ?)");
  dht.begin();

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  scanNetworks();
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onCommand);
  mqtt.setKeepAlive(15);
}

void loop() {
  uint32_t now = millis();

  if (!mqtt.connected() && now - tReconnect >= RECONNECT_MS) {
    tReconnect = now;
    connectNetwork();
  }
  mqtt.loop();

  checkPir();                       // réagit en continu, sans attendre les 2 s

  if (now - tTele >= TELEMETRY_MS) {
    tTele = now;
    readSensors();
    publishTelemetry();
  }
  if (now - tOled >= OLED_MS) {
    tOled = now;
    drawOled();
  }
}

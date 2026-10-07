#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// Configuration du capteur DHT (humidité et température)
const int DHT_PIN = D5;
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);

// Configuration du Wi-Fi
const char *WIFI_SSID = "Jul’s iPhone";
const char *WIFI_PASSWORD = "00000000";

// Configuration du broker MQTT
const char *MQTT_BROKER = "172.20.10.4";
const int MQTT_PORT = 1883;

// Identifiant unique de l'appareil
const char *DEVICE_ID = "esp8266-01";

const int ledBleu = D0; // Pin de la LED bleue
const int MQ2_PIN = A0; // Sortie analogique du MQ-2
const int PIR_PIN = D6; // Pin du capteur PIR

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void connectWiFi()
{
  Serial.print("Connexion au Wi-Fi");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  digitalWrite(ledBleu, HIGH);

  Serial.println();
  Serial.println("Wi-Fi connecte !");
  Serial.print("Adresse IP : ");
  Serial.println(WiFi.localIP());
}

void connectMQTT()
{
  while (!mqttClient.connected())
  {
    Serial.print("Connexion au broker MQTT... ");

    if (mqttClient.connect(DEVICE_ID))
    {
      Serial.println("MQTT connecte !");

      if (mqttClient.publish(
              "sentinel/esp8266/status",
              "online"))
      {
        Serial.println("MQTT status publie");
      }
    }
    else
    {
      Serial.print("ECHEC, code = ");
      Serial.println(mqttClient.state());

      delay(2000);
    }
  }
}

void publishTelemetry()
{
  // Données de température et d'humidité du DHT22
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Lecture réelle du MQ-2
  int gas = analogRead(MQ2_PIN);

  // Lecture de la présence du capteur PIR
  bool presence = digitalRead(PIR_PIN);

  if (isnan(temperature) || isnan(humidity))
  {
    Serial.println("Erreur lecture DHT22");
    return;
  }

  char payload[256];

  snprintf(
      payload,
      sizeof(payload),
      "{\"device_id\":\"%s\",\"temperature\":%.1f,\"humidity\":%.1f,\"gas\":%d,\"presence\":%s}",
      DEVICE_ID,
      temperature,
      humidity,
      gas,
      presence ? "true" : "false");

  if (mqttClient.publish(
          "sentinel/esp8266/telemetry",
          payload))
  {
    Serial.print("Telemetry -> ");
    Serial.println(payload);
  }
  else
  {
    Serial.println("Erreur publication telemetry");
  }
}

void setup()
{
  Serial.begin(115200);

  dht.begin();

  pinMode(ledBleu, OUTPUT);
  pinMode(PIR_PIN, INPUT);

  Serial.println();
  Serial.println("================================");
  Serial.println("       SENTINEL-X IoT");
  Serial.println("================================");

  connectWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  connectMQTT();
}

void loop()
{
  if (!mqttClient.connected())
  {
    connectMQTT();
  }

  mqttClient.loop();

  static unsigned long lastMessage = 0;

  if (millis() - lastMessage >= 5000)
  {
    lastMessage = millis();

    publishTelemetry();
  }
}
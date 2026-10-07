#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char *WIFI_SSID = "Jul’s iPhone";
const char *WIFI_PASSWORD = "00000000";

const char *MQTT_BROKER = "172.20.10.4";
const int MQTT_PORT = 1883;

const char *DEVICE_ID = "esp8266-01";

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
  // Données simulées pour le moment
  float temperature = 20.6;
  float humidity = 50.3;
  int gas = 183;
  bool presence = true;

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

  pinMode(D0, OUTPUT);

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
  digitalWrite(D0, HIGH);  // LED allumée
  delay(500);
  digitalWrite(D0, LOW);   // LED éteinte
  delay(500);

  
  if (!mqttClient.connected())
  {
    connectMQTT();
  }

  mqttClient.loop();

  static unsigned long lastMessage = 0;

  if (millis() - lastMessage >= 50000)
  {
    lastMessage = millis();

    publishTelemetry();
  }
}
// ============================================================================
// SENTINEL-X — Firmware ESP8266 / Wemos D1 mini
// ============================================================================
//
// Capteurs :
//   DHT22  -> température / humidité
//   PIR    -> détection de mouvement
//   MQ-2   -> niveau de gaz
//
// Sorties :
//   OLED       -> état du système
//   LED rouge  -> alerte gaz clignotante
//   LED bleue  -> présence
//
// MQTT :
//   sentinel/esp8266/telemetry
//   sentinel/esp8266/events
//   sentinel/esp8266/status
//   sentinel/esp8266/cmd
//
// ============================================================================

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#include "secrets.h"

// ============================================================================
// IDENTITÉ
// ============================================================================

#define DEVICE_ID "esp8266-01"

// ============================================================================
// MQTT TOPICS
// ============================================================================

#define TOPIC_TELEMETRY "sentinel/esp8266/telemetry"
#define TOPIC_EVENTS    "sentinel/esp8266/events"
#define TOPIC_STATUS    "sentinel/esp8266/status"
#define TOPIC_CMD       "sentinel/esp8266/cmd"

// ============================================================================
// BROCHES
// ============================================================================

// DHT22
#define PIN_DHT D5

// PIR
#define PIN_PIR D6

// MQ-2
#define PIN_GAS A0

// LED rouge
// patte longue -> résistance 220 ohms -> D3
// patte courte -> GND
#define PIN_LED_RED D3

// LED bleue
#define PIN_LED_BLUE D0

// LED rouge : HIGH = ON
#define LED_RED_ON HIGH
#define LED_RED_OFF LOW

// LED bleue : LOW = ON
#define LED_BLUE_ON LOW
#define LED_BLUE_OFF HIGH

// ============================================================================
// RÉGLAGES
// ============================================================================

// Publication périodique
#define TELEMETRY_MS 2000

// Rafraîchissement OLED
#define OLED_MS 500

// Tentative de reconnexion MQTT
#define RECONNECT_MS 5000

// Seuils MQ-2
#define GAS_ALARM_ON 50
#define GAS_ALARM_OFF 45

// Temps de chauffe du MQ-2
#define MQ2_WARMUP_MS 60000

// Vitesse de clignotement LED rouge
#define RED_BLINK_MS 300

// ============================================================================
// OBJETS
// ============================================================================

Adafruit_SSD1306 oled(128, 64, &Wire, -1);

DHT dht(PIN_DHT, DHT22);

WiFiClient net;

PubSubClient mqtt(net);

// ============================================================================
// ÉTAT DU SYSTÈME
// ============================================================================

bool oledOk = false;

float lastTemp = NAN;
float lastHum = NAN;

int lastGas = 0;

bool presence = false;

bool gasAlarm = false;

// Commande LED bleue depuis le dashboard
bool cmdLed = false;

// État de la LED rouge
bool redLedState = false;

// Timers
uint32_t tTele = 0;
uint32_t tOled = 0;
uint32_t tReconnect = 0;
uint32_t tRedBlink = 0;

// Statistiques
uint32_t dhtErrors = 0;

// ============================================================================
// SORTIES
// ============================================================================

void updateRedLed()
{
    // Pas d'alarme :
    // LED rouge éteinte
    if (!gasAlarm)
    {
        digitalWrite(PIN_LED_RED, LED_RED_OFF);
        redLedState = false;
        return;
    }

    uint32_t now = millis();

    // Clignotement non bloquant
    if (now - tRedBlink >= RED_BLINK_MS)
    {
        tRedBlink = now;

        redLedState = !redLedState;

        digitalWrite(
            PIN_LED_RED,
            redLedState ? LED_RED_ON : LED_RED_OFF
        );
    }
}

void applyOutputs()
{
    // ------------------------------------------------------------------------
    // LED bleue
    // ------------------------------------------------------------------------
    //
    // La LED bleue indique :
    // - une présence détectée
    // - ou une commande manuelle depuis le dashboard
    //

    digitalWrite(
        PIN_LED_BLUE,
        (cmdLed || presence)
            ? LED_BLUE_OFF
            : LED_BLUE_ON
    );

    // ------------------------------------------------------------------------
    // LED rouge
    // ------------------------------------------------------------------------
    //
    // La LED rouge clignote uniquement lorsqu'une alarme gaz est active.
    //

    updateRedLed();
}

// ============================================================================
// ÉVÉNEMENTS MQTT
// ============================================================================

void publishEvent(
    const char *type,
    const char *state,
    int value
)
{
    char buffer[160];

    snprintf(
        buffer,
        sizeof(buffer),
        "{\"device_id\":\"%s\",\"type\":\"%s\",\"state\":\"%s\",\"value\":%d}",
        DEVICE_ID,
        type,
        state,
        value
    );

    if (mqtt.connected())
    {
        mqtt.publish(
            TOPIC_EVENTS,
            buffer
        );
    }

    Serial.printf(
        "[EVENT] %s\n",
        buffer
    );
}

// ============================================================================
// TÉLÉMÉTRIE
// ============================================================================

void publishTelemetry()
{
    // On ne publie pas tant qu'on n'a pas
    // une mesure DHT22 valide.

    if (isnan(lastTemp) || isnan(lastHum))
    {
        Serial.println(
            "[TELE] DHT22 non disponible"
        );

        return;
    }

    char buffer[200];

    snprintf(
        buffer,
        sizeof(buffer),
        "{\"device_id\":\"%s\",\"temperature\":%.1f,\"humidity\":%.1f,\"gas\":%d,\"presence\":%s}",
        DEVICE_ID,
        lastTemp,
        lastHum,
        lastGas,
        presence ? "true" : "false"
    );

    bool sent =
        mqtt.connected() &&
        mqtt.publish(
            TOPIC_TELEMETRY,
            buffer
        );

    Serial.printf(
        "[TELE] %s %s\n",
        sent ? "->" : "(non envoyé)",
        buffer
    );
}

// ============================================================================
// COMMANDES MQTT
// ============================================================================

void onCommand(
    char *topic,
    byte *payload,
    unsigned int length
)
{
    char message[96];

    length = min(
        length,
        (unsigned int)sizeof(message) - 1
    );

    memcpy(
        message,
        payload,
        length
    );

    message[length] = '\0';

    Serial.printf(
        "[CMD] %s\n",
        message
    );

    // Exemple accepté :
    //
    // {"led":"on"}
    // {"led":"off"}

    bool on =
        strstr(message, "\"on\"") ||
        strstr(message, "true");

    if (strstr(message, "led"))
    {
        cmdLed = on;
    }

    applyOutputs();
}

// ============================================================================
// ÉTAT WI-FI
// ============================================================================

const char *wifiStatus()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        return "OK";
    }

    return "OFF";
}

// ============================================================================
// CONNEXION MQTT
// ============================================================================

void connectMQTT()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        return;
    }

    if (mqtt.connected())
    {
        return;
    }

    Serial.printf(
        "[MQTT] connexion a %s:%d...\n",
        MQTT_HOST,
        MQTT_PORT
    );

    const char *user =
        strlen(MQTT_USER)
            ? MQTT_USER
            : nullptr;

    const char *pass =
        strlen(MQTT_PASS)
            ? MQTT_PASS
            : nullptr;

    // Last Will
    if (
        mqtt.connect(
            DEVICE_ID,
            user,
            pass,
            TOPIC_STATUS,
            1,
            true,
            "offline"
        )
    )
    {
        Serial.println(
            "[MQTT] connecte"
        );

        // Statut online retenu
        mqtt.publish(
            TOPIC_STATUS,
            "online",
            true
        );

        // Écoute des commandes
        mqtt.subscribe(
            TOPIC_CMD,
            1
        );
    }
    else
    {
        Serial.printf(
            "[MQTT] erreur rc=%d\n",
            mqtt.state()
        );
    }
}

// ============================================================================
// LECTURE DES CAPTEURS
// ============================================================================

void readSensors()
{
    // ------------------------------------------------------------------------
    // DHT22
    // ------------------------------------------------------------------------

    float temperature =
        dht.readTemperature();

    float humidity =
        dht.readHumidity();

    if (
        !isnan(temperature) &&
        !isnan(humidity)
    )
    {
        lastTemp = temperature;
        lastHum = humidity;
    }
    else
    {
        dhtErrors++;

        Serial.printf(
            "[DHT] erreur de lecture (%lu)\n",
            (unsigned long)dhtErrors
        );
    }

    // ------------------------------------------------------------------------
    // MQ-2
    // ------------------------------------------------------------------------

    lastGas =
        analogRead(PIN_GAS);

    // ------------------------------------------------------------------------
    // Alarme gaz
    // ------------------------------------------------------------------------

    // Pendant le temps de chauffe :
    // aucune alarme gaz.

    if (millis() >= MQ2_WARMUP_MS)
    {
        // Déclenchement
        if (
            !gasAlarm &&
            lastGas >= GAS_ALARM_ON
        )
        {
            gasAlarm = true;

            Serial.println(
                "[GAS] ALARME GAZ !"
            );

            publishEvent(
                "GAS",
                "TRIGGERED",
                lastGas
            );
        }

        // Acquittement
        else if (
            gasAlarm &&
            lastGas <= GAS_ALARM_OFF
        )
        {
            gasAlarm = false;

            Serial.println(
                "[GAS] Alarme gaz terminée"
            );

            publishEvent(
                "GAS",
                "CLEARED",
                lastGas
            );
        }
    }

    applyOutputs();
}

// ============================================================================
// PIR
// ============================================================================

void checkPir()
{
    bool detected =
        digitalRead(PIN_PIR) == HIGH;

    // Aucun changement
    if (detected == presence)
    {
        return;
    }

    presence = detected;

    publishEvent(
        "PIR",
        presence
            ? "TRIGGERED"
            : "CLEARED",
        presence ? 1 : 0
    );

    applyOutputs();

    // On informe immédiatement le dashboard.
    publishTelemetry();
}

// ============================================================================
// OLED
// ============================================================================

void drawOled()
{
    if (!oledOk)
    {
        return;
    }

    oled.clearDisplay();

    oled.setTextColor(
        SSD1306_WHITE
    );

    // ------------------------------------------------------------------------
    // Ligne 1 : Wi-Fi
    // ------------------------------------------------------------------------

    oled.setTextSize(1);
    oled.setCursor(0, 0);

    oled.print("WiFi: ");

    if (WiFi.status() == WL_CONNECTED)
    {
        oled.print("OK");
    }
    else
    {
        oled.print("OFF");
    }

    // MQTT
    oled.setCursor(92, 0);

    oled.print(
        mqtt.connected()
            ? "MQTT"
            : "---"
    );

    // ------------------------------------------------------------------------
    // Ligne 2 : IP
    // ------------------------------------------------------------------------

    oled.setCursor(0, 10);

    if (WiFi.status() == WL_CONNECTED)
    {
        oled.print(
            WiFi.localIP().toString()
        );
    }
    else
    {
        oled.print("IP: ---");
    }

    // Séparation
    oled.drawLine(
        0,
        20,
        127,
        20,
        SSD1306_WHITE
    );

    // ------------------------------------------------------------------------
    // Température
    // ------------------------------------------------------------------------

    oled.setTextSize(1);
    oled.setCursor(0, 24);

    if (isnan(lastTemp))
    {
        oled.print("Temp: --.- C");
    }
    else
    {
        oled.printf(
            "Temp: %.1f C",
            lastTemp
        );
    }

    // ------------------------------------------------------------------------
    // Humidité
    // ------------------------------------------------------------------------

    oled.setCursor(0, 34);

    if (isnan(lastHum))
    {
        oled.print("Hum : --.- %");
    }
    else
    {
        oled.printf(
            "Hum : %.1f %%",
            lastHum
        );
    }

    // ------------------------------------------------------------------------
    // Gaz
    // ------------------------------------------------------------------------

    oled.setCursor(0, 44);

    oled.printf(
        "Gaz : %d",
        lastGas
    );

    // ------------------------------------------------------------------------
    // PIR
    // ------------------------------------------------------------------------

    oled.setCursor(70, 44);

    oled.print("PIR:");

    oled.print(
        presence
            ? "ON"
            : "OFF"
    );

    // ------------------------------------------------------------------------
    // État global
    // ------------------------------------------------------------------------

    oled.setCursor(0, 55);

    if (gasAlarm)
    {
        oled.print("!! ALERTE GAZ !!");
    }
    else if (presence)
    {
        oled.print("! PRESENCE !");
    }
    else if (WiFi.status() != WL_CONNECTED)
    {
        oled.print("WiFi OFF");
    }
    else if (!mqtt.connected())
    {
        oled.print("MQTT OFF");
    }
    else
    {
        oled.print("Etat: OK");
    }

    oled.display();
}

// ============================================================================
// SETUP
// ============================================================================

void setup()
{
    Serial.begin(115200);

    delay(200);

    Serial.println();

    Serial.println(
        "================================"
    );

    Serial.println(
        "       SENTINEL-X IoT"
    );

    Serial.println(
        "================================"
    );

    // ------------------------------------------------------------------------
    // GPIO
    // ------------------------------------------------------------------------

    pinMode(
        PIN_PIR,
        INPUT
    );

    pinMode(
        PIN_LED_RED,
        OUTPUT
    );

    pinMode(
        PIN_LED_BLUE,
        OUTPUT
    );

    // État initial
    digitalWrite(
        PIN_LED_RED,
        LED_RED_OFF
    );

    digitalWrite(
        PIN_LED_BLUE,
        LED_BLUE_OFF
    );

    // ------------------------------------------------------------------------
    // OLED
    // ------------------------------------------------------------------------

    Wire.begin(
        D2, // SDA
        D1  // SCL
    );

    oledOk =
        oled.begin(
            SSD1306_SWITCHCAPVCC,
            0x3C
        );

    if (oledOk)
    {
        Serial.println(
            "[OLED] OK"
        );

        oled.clearDisplay();

        oled.setTextColor(
            SSD1306_WHITE
        );

        oled.setTextSize(2);

        oled.setCursor(0, 0);

        oled.println(
            "SENTINEL-X"
        );

        oled.setTextSize(1);

        oled.println();

        oled.println(
            "Initialisation..."
        );

        oled.display();
    }
    else
    {
        Serial.println(
            "[OLED] absent"
        );
    }

    // ------------------------------------------------------------------------
    // DHT22
    // ------------------------------------------------------------------------

    dht.begin();

    // ------------------------------------------------------------------------
    // Wi-Fi
    // ------------------------------------------------------------------------

    WiFi.mode(WIFI_STA);

    WiFi.setAutoReconnect(
        true
    );

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASS
    );

    Serial.printf(
        "[WIFI] connexion a %s...\n",
        WIFI_SSID
    );

    // ------------------------------------------------------------------------
    // MQTT
    // ------------------------------------------------------------------------

    mqtt.setServer(
        MQTT_HOST,
        MQTT_PORT
    );

    mqtt.setCallback(
        onCommand
    );

    mqtt.setKeepAlive(
        15
    );
}

// ============================================================================
// LOOP
// ============================================================================

void loop()
{
    uint32_t now =
        millis();

    // ------------------------------------------------------------------------
    // MQTT
    // ------------------------------------------------------------------------

    if (
        !mqtt.connected() &&
        now - tReconnect >= RECONNECT_MS
    )
    {
        tReconnect = now;

        connectMQTT();
    }

    mqtt.loop();

    // ------------------------------------------------------------------------
    // LED rouge
    // ------------------------------------------------------------------------
    //
    // Important : appelé en permanence pour que le clignotement
    // soit indépendant de la lecture des capteurs.
    //

    updateRedLed();

    // ------------------------------------------------------------------------
    // PIR
    // ------------------------------------------------------------------------
    //
    // Surveillance continue.
    // Pas besoin d'attendre les 2 secondes.
    //

    checkPir();

    // ------------------------------------------------------------------------
    // Télémétrie
    // ------------------------------------------------------------------------

    if (
        now - tTele >= TELEMETRY_MS
    )
    {
        tTele = now;

        readSensors();

        publishTelemetry();
    }

    // ------------------------------------------------------------------------
    // OLED
    // ------------------------------------------------------------------------

    if (
        now - tOled >= OLED_MS
    )
    {
        tOled = now;

        drawOled();
    }
}
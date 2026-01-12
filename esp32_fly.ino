#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

/* ============ WIFI ============ */
const char* ssid = "Fly";
const char* password = "123456789";

/* ============ RELAY (ACTIVE HIGH) ============ */
#define RELAY_PIN 4

WebServer server(80);

/* ============ PULSE CONTROL ============ */
bool pulseMode = false;
bool relayState = false;
unsigned long lastToggle = 0;
const unsigned long pulseInterval = 2500; // 2.5 วินาที

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  WiFi.begin(ssid, password);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    if (millis() - start > 15000) ESP.restart();
  }

  Serial.println("WiFi Connected");
  Serial.println(WiFi.localIP());

  /* ===== CONTROL API ===== */
  server.on("/control", HTTP_POST, []() {
    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, server.arg("plain"))) {
      server.send(400, "application/json", "{\"error\":\"bad json\"}");
      return;
    }

    String action = doc["action"] | "";

    if (action == "ON") {
      pulseMode = true;
      relayState = true;
      lastToggle = millis();
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("PULSE MODE ON");
    }

    if (action == "OFF") {
      pulseMode = false;
      relayState = false;
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("PULSE MODE OFF");
    }

    server.send(200, "application/json", "{\"status\":\"ok\"}");
  });

  server.on("/status", HTTP_GET, []() {
    StaticJsonDocument<100> doc;
    doc["pulse"] = pulseMode;
    doc["relay"] = relayState ? "ON" : "OFF";
    String res;
    serializeJson(doc, res);
    server.send(200, "application/json", res);
  });

  server.begin();
  Serial.println("Control Server Ready");
}

void loop() {
  server.handleClient();

  if (pulseMode && millis() - lastToggle >= pulseInterval) {
    relayState = !relayState;
    digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
    lastToggle = millis();

    Serial.println(relayState ? "RELAY ON" : "RELAY OFF");
  }
}

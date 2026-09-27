/*
 * BheedRakshak AI — ESP32 Output Controller Firmware
 *
 * Hardware components:
 *   - OLED (SSD1306 I2C 128x64): SDA=GPIO21, SCL=GPIO22
 *   - Green LED:  GPIO27
 *   - Yellow LED: GPIO14
 *   - Red LED:    GPIO32
 *   - Buzzer:     GPIO33
 *
 * Required Libraries (Install via Arduino IDE Library Manager):
 *   1. "Adafruit SSD1306" by Adafruit
 *   2. "Adafruit GFX Library" by Adafruit
 *   (WiFi.h, WebServer.h, Wire.h are built into the ESP32 Arduino core)
 */

#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ==========================================
// 1. Wi-Fi Configuration (Edit these)
// ==========================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ==========================================
// 2. Hardware Pin Definitions
// ==========================================
#define OLED_SDA_PIN   21
#define OLED_SCL_PIN   22
#define LED_GREEN_PIN  27
#define LED_YELLOW_PIN 14
#define LED_RED_PIN    32
#define BUZZER_PIN     33

#define SCREEN_WIDTH   128
#define SCREEN_HEIGHT  64
#define OLED_RESET     -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
WebServer server(80);

// ==========================================
// 3. State Variables
// ==========================================
String currentRiskState = "NORMAL";
String currentExitState = "";

// Non-blocking buzzer state machine
enum BuzzerMode {
  BUZZ_IDLE,
  BUZZ_ONE_BEEP,
  BUZZ_TWO_BEEPS,
  BUZZ_THREE_BEEPS,
  BUZZ_CRITICAL_PULSE
};

BuzzerMode buzzerMode = BUZZ_IDLE;
unsigned long buzzerTimer = 0;
int buzzerStep = 0;

// ==========================================
// 4. OLED Helper
// ==========================================
void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // Title Header
  display.setTextSize(1);
  display.setCursor(10, 2);
  display.print("BHEEDRAKSHAK AI");
  display.drawLine(0, 12, 127, 12, SSD1306_WHITE);

  // Risk Level
  display.setTextSize(1);
  display.setCursor(0, 18);
  display.print("Risk Level:");
  
  display.setTextSize(2);
  display.setCursor(0, 28);
  display.print(currentRiskState);

  // Exit Instruction (if active)
  display.setTextSize(1);
  display.setCursor(0, 48);
  if (currentExitState.length() > 0) {
    display.print("-> ");
    display.print(currentExitState);
  } else {
    display.print("Status: Monitoring");
  }

  display.display();
}

// ==========================================
// 5. LED Control Helper
// ==========================================
void applyRiskLEDs(String risk) {
  if (risk == "NORMAL") {
    digitalWrite(LED_GREEN_PIN, HIGH);
    digitalWrite(LED_YELLOW_PIN, LOW);
    digitalWrite(LED_RED_PIN, LOW);
  } else if (risk == "WARNING") {
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_YELLOW_PIN, HIGH);
    digitalWrite(LED_RED_PIN, LOW);
  } else if (risk == "HIGH" || risk == "CRITICAL") {
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_YELLOW_PIN, LOW);
    digitalWrite(LED_RED_PIN, HIGH);
  }
}

// ==========================================
// 6. Non-Blocking Buzzer Engine (millis-based)
// ==========================================
void triggerBuzzer(BuzzerMode mode) {
  buzzerMode = mode;
  buzzerStep = 0;
  buzzerTimer = millis();
  digitalWrite(BUZZER_PIN, LOW);
}

void updateBuzzer() {
  unsigned long now = millis();

  switch (buzzerMode) {
    case BUZZ_IDLE:
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case BUZZ_ONE_BEEP:
      if (buzzerStep == 0) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 1;
        buzzerTimer = now;
      } else if (buzzerStep == 1 && (now - buzzerTimer >= 150)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerMode = BUZZ_IDLE;
      }
      break;

    case BUZZ_TWO_BEEPS:
      if (buzzerStep == 0) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 1;
        buzzerTimer = now;
      } else if (buzzerStep == 1 && (now - buzzerTimer >= 100)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerStep = 2;
        buzzerTimer = now;
      } else if (buzzerStep == 2 && (now - buzzerTimer >= 80)) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 3;
        buzzerTimer = now;
      } else if (buzzerStep == 3 && (now - buzzerTimer >= 100)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerMode = BUZZ_IDLE;
      }
      break;

    case BUZZ_THREE_BEEPS:
      if (buzzerStep == 0) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 1;
        buzzerTimer = now;
      } else if (buzzerStep == 1 && (now - buzzerTimer >= 80)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerStep = 2;
        buzzerTimer = now;
      } else if (buzzerStep == 2 && (now - buzzerTimer >= 60)) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 3;
        buzzerTimer = now;
      } else if (buzzerStep == 3 && (now - buzzerTimer >= 80)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerStep = 4;
        buzzerTimer = now;
      } else if (buzzerStep == 4 && (now - buzzerTimer >= 60)) {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerStep = 5;
        buzzerTimer = now;
      } else if (buzzerStep == 5 && (now - buzzerTimer >= 80)) {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerMode = BUZZ_IDLE;
      }
      break;

    case BUZZ_CRITICAL_PULSE:
      // Repeating 200ms ON / 200ms OFF while in CRITICAL state
      if ((now - buzzerTimer) >= 200) {
        buzzerTimer = now;
        int currentLevel = digitalRead(BUZZER_PIN);
        digitalWrite(BUZZER_PIN, currentLevel == HIGH ? LOW : HIGH);
      }
      break;
  }
}

// ==========================================
// 7. HTTP Command Handler: /command?action=X
// ==========================================
void handleCommand() {
  if (!server.hasArg("action")) {
    server.send(400, "text/plain", "Missing action parameter");
    return;
  }

  String action = server.arg("action");
  action.toUpperCase();
  Serial.print("[HTTP] Received command: ");
  Serial.println(action);

  if (action == "NORMAL") {
    currentRiskState = "NORMAL";
    currentExitState = "";
    applyRiskLEDs("NORMAL");
    triggerBuzzer(BUZZ_IDLE);
    updateDisplay();
  } else if (action == "WARNING") {
    currentRiskState = "WARNING";
    applyRiskLEDs("WARNING");
    triggerBuzzer(BUZZ_IDLE);
    updateDisplay();
  } else if (action == "HIGH") {
    currentRiskState = "HIGH";
    applyRiskLEDs("HIGH");
    triggerBuzzer(BUZZ_ONE_BEEP);
    updateDisplay();
  } else if (action == "CRITICAL") {
    currentRiskState = "CRITICAL";
    applyRiskLEDs("CRITICAL");
    triggerBuzzer(BUZZ_CRITICAL_PULSE);
    updateDisplay();
  } else if (action == "OPEN_EXIT_1") {
    currentExitState = "USE EXIT 1";
    triggerBuzzer(BUZZ_TWO_BEEPS);
    updateDisplay();
  } else if (action == "OPEN_EXIT_2") {
    currentExitState = "USE EXIT 2";
    triggerBuzzer(BUZZ_THREE_BEEPS);
    updateDisplay();
  } else if (action == "CLOSE_EXITS") {
    currentExitState = "";
    updateDisplay();
  } else {
    server.send(400, "text/plain", "Unknown action");
    return;
  }

  server.send(200, "text/plain", "OK");
}

// ==========================================
// 8. Setup & Main Loop
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n--- BheedRakshak AI Hardware Controller Starting ---");

  // Initialize GPIO Pins
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  // Initialize I2C and OLED
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("[ERROR] SSD1306 OLED allocation failed");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 10);
    display.println("BheedRakshak AI");
    display.println("Connecting Wi-Fi...");
    display.display();
  }

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }

  Serial.println("\n[Wi-Fi] Connected successfully!");
  Serial.print("[Wi-Fi] Assigned IP Address: http://");
  Serial.println(WiFi.localIP());

  // Setup Web Server Routes
  server.on("/command", handleCommand);
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not Found");
  });

  server.begin();
  Serial.println("[HTTP] WebServer started on port 80");

  // Initial State: NORMAL
  applyRiskLEDs("NORMAL");
  updateDisplay();
}

void loop() {
  server.handleClient();
  updateBuzzer();
}

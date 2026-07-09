#include <WiFi.h> // Fixed: Changed from esp_wifi.h to WiFi.h
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

const char* ssid = "HUAWEI";
const char* password = "Pinsara@2003";

WebServer server(80);

// Fixed: Changed to capital 'M' so it matches the rest of your code
Servo frontMotor; 
const int servoPin = 18;

void turnMotor(int deg){
  if(deg < 0) deg = 0;
  if(deg > 180) deg = 180;

  frontMotor.write(deg);
  delay(500);
}

// py api handler
void handleExecuteMoves(){

  if (server.hasArg("plain") == false) {
    server.send(400, "text/plain", "Body not received");
    return;
  }

  // tell py got msg
  server.send(200, "text/plain", "Move received");

  // Fixed: Re-added the missing string declaration
  String jsonPayload = server.arg("plain");

  // --- UPDATED FOR ARDUINOJSON VERSION 7 ---
  JsonDocument doc; 
  DeserializationError error = deserializeJson(doc, jsonPayload);
  // -----------------------------------------
  
  if (error) {
    Serial.println("JSON parsing failed!");
    return;
  }

  JsonArray moves = doc["moves"];
  Serial.println("Starting solve sequence...");

  for (JsonVariant move : moves) {
    String m = move.as<String>();
    Serial.print("Executing: ");
    Serial.println(m);

    // If the move is for the Front face (F), trigger the SG90!
    if (m.charAt(0) == 'F') {
      
      if (m.length() == 1) {
        // "F" -> 180 degrees
        turnMotor(180); 
      } 
      else if (m.charAt(1) == '\'') {
        // "F'" -> 0 degrees
        turnMotor(0); 
      } 
      else if (m.charAt(1) == '2') {
        // "F2" -> Double turn
        turnMotor(180);
        delay(200);
        turnMotor(0);
      }
      
      // Return motor to neutral (90)
      turnMotor(90);
      delay(300);
    } 
    else {
      // It's a different motor's turn, so just wait
      Serial.println(" -> (Waiting for imaginary motor to finish)");
      delay(400); 
    }
  }
  
  Serial.println("Sequence Complete!");
}

// --- MANUAL TEST DASHBOARD ---
void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">";
  html += "<style>body{font-family:sans-serif; text-align:center; background:#222; color:#fff;} ";
  html += "button{background:#007bff; color:white; border:none; padding:20px; margin:10px; font-size:24px; border-radius:8px; width:80%; cursor:pointer;} ";
  html += "button:active{background:#0056b3;}</style></head><body>";
  html += "<h1>SG90 Test Dashboard</h1>";
  
  html += "<button onclick=\"fetch('/test?angle=0')\">0 Deg</button>";
  html += "<button style=\"background:#28a745\" onclick=\"fetch('/test?angle=90')\">90 Deg</button>";
  html += "<button onclick=\"fetch('/test?angle=180')\">180 Deg</button>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

void handleTest() {
  if (server.hasArg("angle")) {
    int targetAngle = server.arg("angle").toInt();
    turnMotor(targetAngle);
    server.send(200, "text/plain", "Moved");
  }
}

void setup() {
  Serial.begin(115200);

  // --- SG90 CALIBRATION ---
  // Allow allocation of all timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  frontMotor.setPeriodHertz(50); // Standard 50hz servo
  
  // SG90 servos usually prefer pulses between ~500 and ~2400
  // If your servo buzzes at 0 or 180, adjust these numbers!
  frontMotor.attach(servoPin, 500, 2400); 
  
  turnMotor(90); // Start at 90 degrees

  Serial.print("Connecting to Wi-Fi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n--- CONNECTED! ---");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP()); 

  server.on("/", HTTP_GET, handleRoot);
  server.on("/test", HTTP_GET, handleTest);
  server.on("/execute", HTTP_POST, handleExecuteMoves);
  
  server.begin();
}

void loop() {
  server.handleClient();
}
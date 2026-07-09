#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin(); // Uses default SDA (21) and SCL (22) on ESP32
  Serial.println("\nI2C Scanner is ready.");
}

void loop() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Scanning...");

  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("SUCCESS: PCA9685 found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      nDevices++;
    }
  }
  
  if (nDevices == 0) {
    Serial.println("ERROR: No I2C devices found. Check wiring!");
  }
  delay(5000); // Wait 5 seconds and scan again
}
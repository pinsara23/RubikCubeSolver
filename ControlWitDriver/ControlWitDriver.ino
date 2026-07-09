#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Initialize the PCA9685
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// --- Map Motors to PCA9685 Channels (0 through 7) ---
const int ROT_F = 4;
const int ROT_B = 5;
const int ROT_L = 7;
const int ROT_R = 6;

const int GRIP_F = 2;
const int GRIP_B = 1;
const int GRIP_L = 3;
const int GRIP_R = 0;

// Function to convert angle to precise microsecond pulse for PCA9685
void turnMotor(uint8_t channel, int degrees) {
  
  
  // Map 0-180 degrees to the exact 500-2400 microsecond range
  int microsec = map(degrees, 0, 180, 500, 2400);
  
  // Send the precise microsecond pulse to the driver board
  pwm.writeMicroseconds(channel, microsec);
  
  delay(10); // Tiny delay to prevent I2C bus flooding
}

void setup() {
  Serial.begin(115200);

  // Start the I2C connection and PCA9685
  Wire.begin(); // SDA = 21, SCL = 22
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz

  // Move all to neutral starting positions (90 degrees)
  turnMotor(ROT_F, 92); turnMotor(ROT_B, 90); turnMotor(ROT_L, 91); turnMotor(ROT_R, 81);
  turnMotor(GRIP_F,0); turnMotor(GRIP_B, -5); turnMotor(GRIP_L, -10); turnMotor(GRIP_R, 0);

  Serial.println("\n--- 8-SERVO ROBOT READY (PCA9685) ---");
  Serial.println("Listening on USB for commands...");
}

void loop() {
  // Listen for commands coming from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.length() > 0) {
      int colonIndex = command.indexOf(':');
      if (colonIndex > 0) {
        String motorName = command.substring(0, colonIndex);
        int angle = command.substring(colonIndex + 1).toInt();

        // Route the command to the correct channel
        if (motorName == "rotF") turnMotor(ROT_F, angle);
        else if (motorName == "rotB") turnMotor(ROT_B, angle);
        else if (motorName == "rotL") turnMotor(ROT_L, angle);
        else if (motorName == "rotR") turnMotor(ROT_R, angle);
        else if (motorName == "gripF") turnMotor(GRIP_F, angle);
        else if (motorName == "gripB") turnMotor(GRIP_B, angle);
        else if (motorName == "gripL") turnMotor(GRIP_L, angle);
        else if (motorName == "gripR") turnMotor(GRIP_R, angle);
        
        Serial.print("Moved ");
        Serial.print(motorName);
        Serial.print(" to ");
        Serial.println(angle);
      }
    }
  }
}
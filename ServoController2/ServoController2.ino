#include <ESP32Servo.h>
 
// Define 8 servos

Servo rotF, rotB, rotL, rotR;  
Servo gripF, gripB, gripL, gripR;

// gpio pins for the 8 servos
const int rot_pin_F = 13;
const int rot_pin_B = 14;
const int rot_pin_L = 26;
const int rot_pin_R = 27;

const int grip_pin_F = 25;
const int grip_pin_B = 33;
const int grip_pin_L = 32;
const int grip_pin_R = 15;

void setup() {

  Serial.begin(115200);

  // allocate hw timers to each servo
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2); 
  ESP32PWM::allocateTimer(3);

  // attach the servos to their respective pins
  rotF.attach(rot_pin_F, 500, 2400); // default min/max is 544, 2400 us
  rotB.attach(rot_pin_B, 500, 2400);
  rotL.attach(rot_pin_L, 500, 2400);
  rotR.attach(rot_pin_R, 500, 2400);

  gripF.attach(grip_pin_F, 500, 2400);
  gripB.attach(grip_pin_B, 500, 2400);
  gripL.attach(grip_pin_L, 500, 2400);
  gripR.attach(grip_pin_R, 500, 2400);

  // for now move all to neutal starting position (Change this after print 3d model and determine the actual neutral position)
  rotF.write(90);
  rotB.write(90);
  rotL.write(90);
  rotR.write(90);

  gripF.write(90);
  gripB.write(90);
  gripL.write(90);
  gripR.write(90);
}

void loop() {
  
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any leading/trailing whitespace

    Serial.print("Received command: ");
    Serial.println(command);

    if (command.length() > 0)
    {
      int colonIndex = command.indexOf(':');
      if (colonIndex > 0) {
        String motorName = command.substring(0, colonIndex);
        int angle = command.substring(colonIndex + 1).toInt();

        //safety check for angle limits
        if (angle < 0) angle = 0;
        if (angle > 180) angle = 180;

        // Route the command
        if (motorName == "rotF") rotF.write(angle);
        else if (motorName == "rotB") rotB.write(angle);
        else if (motorName == "rotL") rotL.write(angle);
        else if (motorName == "rotR") rotR.write(angle);
        else if (motorName == "gripF") gripF.write(angle);
        else if (motorName == "gripB") gripB.write(angle);
        else if (motorName == "gripL") gripL.write(angle);
        else if (motorName == "gripR") gripR.write(angle);

        Serial.print("Moved");
        Serial.print(motorName);
        Serial.print(" to ");
        Serial.print(angle);
      }
    }  
  }
}

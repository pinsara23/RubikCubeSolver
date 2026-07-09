// #include <ESP32Servo.h>

// // Create the Servo object and define the pin
// Servo frontMotor;
// const int servoPin = 18; 

// void turnMotor(int degrees) {
//   if (degrees < 0) degrees = 0;
//   if (degrees > 180) degrees = 180;
  
//   frontMotor.write(degrees);
//   delay(500); // Wait for movement
// }

// void setup() {
//   // Start the USB connection at 115200 baud
//   Serial.begin(115200);

//   // Calibrate the SG90
//   ESP32PWM::allocateTimer(0);
//   ESP32PWM::allocateTimer(1);
//   ESP32PWM::allocateTimer(2);
//   ESP32PWM::allocateTimer(3);
  
//   frontMotor.setPeriodHertz(50);
//   frontMotor.attach(servoPin, 500, 2400); 
  
//   turnMotor(90); // Start at neutral

//   Serial.println("\n--- ESP32 READY ---");
//   Serial.println("Listening for Kociemba moves over USB...");
// }

// void loop() {
//   // Check if Python has sent data through the USB cable
//   if (Serial.available() > 0) {
//     // Read the incoming text until the end of the line
//     String m = Serial.readStringUntil('\n');
//     m.trim(); // Clean up any hidden spaces or newlines

//     if (m.length() > 0) {
//       Serial.print("Received Move: ");
//       Serial.println(m);

//       // Trigger the motor if it's a Front face move
//       if (m.charAt(0) == 'F') {
//         if (m.length() == 1) {
//           turnMotor(180); // "F"
//         } 
//         else if (m.charAt(1) == '\'') {
//           turnMotor(0);   // "F'"
//         } 
//         else if (m.charAt(1) == '2') {
//           turnMotor(180); // "F2"
//           delay(200);
//           turnMotor(0);
//         }
        
//         turnMotor(90); // Return to neutral
//       }
//     }
//   }
// }


#include <ESP32Servo.h>

Servo myServo;
int servoPin = 33; // Use GPIO 18 (labeled as D18 or G18)

void setup() {
  // ESP32 requires specific PWM timer allocation (handled by the library)
  ESP32PWM::allocateTimer(0);
  myServo.setPeriodHertz(50);    // Standard 50hz servo
  myServo.attach(servoPin, 500, 2400); // Attach with min/max pulse widths
}

void loop() {
  //Sweep from 0 to 180 degrees
  for (int pos = 0; pos <= 180; pos += 1) {
    myServo.write(pos);
    delay(15);
  }

  myServo.write(0);
  //myServo.write(180);
  // myServo.write(90);
  // myServo.write(180);

  // myServo.write(90);
  
  // Sweep back from 180 to 0 degrees
  // for (int pos = 180; pos >= 0; pos -= 1) {
  //   myServo.write(pos);
  //   delay(15);
  // }
}
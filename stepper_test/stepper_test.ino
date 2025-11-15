//Includes the Arduino Stepper Library
#include <Stepper.h>

// Defines the number of steps per rotation
const int stepsPerRevolution = 2048;

// Creates 4 stepper motor instances
// Pins entered in sequence IN1-IN3-IN2-IN4 for proper step sequence
// Motor 1
Stepper motor1 = Stepper(stepsPerRevolution, 4, 17, 16, 5);
// Motor 2
Stepper motor2 = Stepper(stepsPerRevolution, 18, 19, 21, 22);
// Motor 3
Stepper motor3 = Stepper(stepsPerRevolution, 23, 25, 26, 27);
// Motor 4
Stepper motor4 = Stepper(stepsPerRevolution, 12, 13, 14, 15);

// ADC configuration
const int adcPin = 34;  // ADC pin (use GPIO 34, 35, 36, or 39 for ESP32)
const int voltageThreshold = 100;  // ADC threshold (0-4095, ~2.5V for 3.3V reference)

int currentSpeed = 8;  // Default speed (1-16 RPM)
bool motorRunning = true;

void setup() {
  Serial.begin(9600);  // Initialize serial communication
  pinMode(adcPin, INPUT);  // Set ADC pin as input
  Serial.println("4-Motor Control Ready");
  Serial.println("Enter speed (1-16) to change motor speed");
  Serial.print("ADC threshold set to: ");
  Serial.println(voltageThreshold);
  
  // Set initial speed for all motors
  motor1.setSpeed(currentSpeed);
  motor2.setSpeed(currentSpeed);
  motor3.setSpeed(currentSpeed);
  motor4.setSpeed(currentSpeed);
}

void loop() {
  // Read ADC value
  int adcValue = analogRead(adcPin);
  Serial.println(adcValue);
  
  // Check if voltage is high (above threshold)
  bool wasRunning = motorRunning;
  if (adcValue >= voltageThreshold) {
    motorRunning = false;
    if (wasRunning) {
      Serial.print("Motor STOPPED - ADC value: ");
      Serial.println(adcValue);
    }
  } else {
    motorRunning = true;
    if (!wasRunning) {
      Serial.print("Motor STARTED - ADC value: ");
      Serial.println(adcValue);
    }
  }
  
  // Check if there's serial input available
  if (Serial.available() > 0) {
    int newSpeed = Serial.parseInt();
    
    // Validate speed is in range 1-16
    if (newSpeed >= 1 && newSpeed <= 16) {
      currentSpeed = newSpeed;
      // Set speed for all motors
      motor1.setSpeed(currentSpeed);
      motor2.setSpeed(currentSpeed);
      motor3.setSpeed(currentSpeed);
      motor4.setSpeed(currentSpeed);
      Serial.print("All motors speed set to: ");
      Serial.println(currentSpeed);
    } else if (newSpeed != 0) {  // Ignore 0 from empty input
      Serial.println("Invalid speed! Enter 1-16");
    }
  }
  
  // Keep all motors running continuously at current speed (only if voltage is low)
  if (motorRunning) {
    motor1.step(10);
    motor2.step(10);
    motor3.step(10);
    motor4.step(10);
  }
}
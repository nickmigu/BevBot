#include <AccelStepper.h>

// ===== STEPPER MOTOR PIN DEFINITIONS =====
// Front Right Motor (Motor 1)
#define FRONT_RIGHT_1  17
#define FRONT_RIGHT_2  5
#define FRONT_RIGHT_3  18
#define FRONT_RIGHT_4  19

// Front Left Motor (Motor 2)
#define FRONT_LEFT_1   26
#define FRONT_LEFT_2   25
#define FRONT_LEFT_3   33
#define FRONT_LEFT_4   32

// Back Right Motor (Motor 3)
#define BACK_RIGHT_1   15
#define BACK_RIGHT_2   2
#define BACK_RIGHT_3   4
#define BACK_RIGHT_4   16

// Back Left Motor (Motor 4)
#define BACK_LEFT_1    13
#define BACK_LEFT_2    12
#define BACK_LEFT_3    14
#define BACK_LEFT_4    27

// ===== CALIBRATION CONSTANTS =====
const int stepsPerRevolution = 2048;
float stepsPerCm = 81.48733;      // Steps needed to move 1cm - jacques cal'd
float stepsPerDegree = 17.77778;  // Steps per motor to rotate robot 1 degree - jacques cal'd

// Wheel diameter and robot dimensions (for reference)
const float wheelDiameter = 8.0;   // cm
const float robotWidth = 25.0;     // cm - wheeltrack
const float robotLength = 16.0;    // cm - wheelbase

// ===== SPEED SETTINGS =====
#define DEFAULT_SPEED 400
#define MAX_SPEED     500


// ===== ACCELSTEPPER MOTOR INSTANCES =====
// Pin sequence: IN1-IN3-IN2-IN4 for proper 28BYJ-48 step sequence
AccelStepper motorFrontRight(AccelStepper::FULL4WIRE, FRONT_RIGHT_1, FRONT_RIGHT_3, FRONT_RIGHT_2, FRONT_RIGHT_4);
AccelStepper motorFrontLeft(AccelStepper::FULL4WIRE, FRONT_LEFT_1, FRONT_LEFT_3, FRONT_LEFT_2, FRONT_LEFT_4);
AccelStepper motorBackRight(AccelStepper::FULL4WIRE, BACK_RIGHT_1, BACK_RIGHT_3, BACK_RIGHT_2, BACK_RIGHT_4);
AccelStepper motorBackLeft(AccelStepper::FULL4WIRE, BACK_LEFT_1, BACK_LEFT_3, BACK_LEFT_2, BACK_LEFT_4);

// ===== ADC CONFIGURATION =====
const int adcPin = 34;
const int voltageThreshold = 800;

// ===== GLOBAL VARIABLES =====
int currentSpeed = DEFAULT_SPEED;  // steps per second
bool motorRunning = true;

// ===== MOVEMENT FUNCTIONS =====

// Move robot forward/backward by distance in cm
void moveLinear(float distanceCm) {
  int steps = (int)(distanceCm * stepsPerCm);
  
  // Set target positions for all motors (same direction for forward/backward)
  motorFrontRight.move(steps);
  motorFrontLeft.move(steps);
  motorBackRight.move(steps);
  motorBackLeft.move(steps);
  
  // Run until all motors reach target
  while (motorFrontRight.distanceToGo() != 0 || 
         motorFrontLeft.distanceToGo() != 0 || 
         motorBackRight.distanceToGo() != 0 || 
         motorBackLeft.distanceToGo() != 0) {
    
    if (!checkADC()) {
      // Stop if ADC threshold exceeded
      motorFrontRight.stop();
      motorFrontLeft.stop();
      motorBackRight.stop();
      motorBackLeft.stop();
      break;
    }
    
    // Non-blocking run - all motors step concurrently
    motorFrontRight.run();
    motorFrontLeft.run();
    motorBackRight.run();
    motorBackLeft.run();
  }
}

// Strafe left/right by distance in cm
void strafe(float distanceCm) {
  int steps = (int)(distanceCm * stepsPerCm);
  
  // For mecanum strafing: diagonal wheels work together
  // Right strafe: FR and BL forward, FL and BR backward
  motorFrontRight.move(steps);
  motorFrontLeft.move(-steps);
  motorBackRight.move(-steps);
  motorBackLeft.move(steps);
  
  // Run until all motors reach target
  while (motorFrontRight.distanceToGo() != 0 || 
         motorFrontLeft.distanceToGo() != 0 || 
         motorBackRight.distanceToGo() != 0 || 
         motorBackLeft.distanceToGo() != 0) {
    
    if (!checkADC()) {
      motorFrontRight.stop();
      motorFrontLeft.stop();
      motorBackRight.stop();
      motorBackLeft.stop();
      break;
    }
    
    motorFrontRight.run();
    motorFrontLeft.run();
    motorBackRight.run();
    motorBackLeft.run();
  }
}

// Rotate robot by theta degrees (positive = clockwise)
void rotate(float thetaDegrees) {
  int steps = (int)(thetaDegrees * stepsPerDegree);
  
  // For rotation: left and right sides turn opposite directions
  motorFrontRight.move(steps);
  motorFrontLeft.move(-steps);
  motorBackRight.move(steps);
  motorBackLeft.move(-steps);
  
  // Run until all motors reach target
  while (motorFrontRight.distanceToGo() != 0 || 
         motorFrontLeft.distanceToGo() != 0 || 
         motorBackRight.distanceToGo() != 0 || 
         motorBackLeft.distanceToGo() != 0) {
    
    if (!checkADC()) {
      motorFrontRight.stop();
      motorFrontLeft.stop();
      motorBackRight.stop();
      motorBackLeft.stop();
      break;
    }
    
    motorFrontRight.run();
    motorFrontLeft.run();
    motorBackRight.run();
    motorBackLeft.run();
  }
}

// ===== UTILITY FUNCTIONS =====

// Check ADC and update motor running state
bool checkADC() {
  int adcValue = analogRead(adcPin);
  
  bool wasRunning = motorRunning;
  if (adcValue >= voltageThreshold) {
    motorRunning = false;
    if (wasRunning) {
      Serial.print("Motor STOPPED - ADC value: ");
      Serial.println(adcValue);
    }
    return false;
  } else {
    motorRunning = true;
    if (!wasRunning) {
      Serial.print("Motor STARTED - ADC value: ");
      Serial.println(adcValue);
    }
    return true;
  }
}

// Stop all motors immediately
void stopAllMotors() {
  motorFrontRight.stop();
  motorFrontLeft.stop();
  motorBackRight.stop();
  motorBackLeft.stop();
  motorRunning = false;
}

// ===== SETUP =====
void setup() {
  Serial.begin(9600);
  pinMode(adcPin, INPUT);
  
  Serial.println("=== Mecanum Wheel Robot Ready (AccelStepper) ===");
  Serial.println("Commands:");
  Serial.println("  Speed (1-1000): Set motor speed (steps/sec)");
  Serial.println("  'f10': Move forward 10cm");
  Serial.println("  'b10': Move backward 10cm");
  Serial.println("  's5': Strafe right 5cm");
  Serial.println("  'l5': Strafe left 5cm");
  Serial.println("  'r90': Rotate 90 degrees clockwise");
  Serial.println("  'c90': Rotate 90 degrees counter-clockwise");
  Serial.println("  'x': Stop all motors");
  Serial.print("ADC threshold: ");
  Serial.println(voltageThreshold);
  
  // Set max speed and acceleration for all motors
  motorFrontRight.setMaxSpeed(MAX_SPEED);
  motorFrontRight.setAcceleration(500.0);
  motorFrontRight.setSpeed(currentSpeed);
  
  motorFrontLeft.setMaxSpeed(MAX_SPEED);
  motorFrontLeft.setAcceleration(500.0);
  motorFrontLeft.setSpeed(currentSpeed);
  
  motorBackRight.setMaxSpeed(MAX_SPEED);
  motorBackRight.setAcceleration(500.0);
  motorBackRight.setSpeed(currentSpeed);
  
  motorBackLeft.setMaxSpeed(MAX_SPEED);
  motorBackLeft.setAcceleration(500.0);
  motorBackLeft.setSpeed(currentSpeed);
  
  Serial.print("Initial speed: ");
  Serial.print(currentSpeed);
  Serial.println(" steps/sec");
}

// ===== MAIN LOOP =====
void loop() {
  // Check ADC
  checkADC();
  
  // Check for serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    // Speed adjustment (numbers only)
    if (command >= '0' && command <= '9') {
      int newSpeed = command - '0';
      
      // Check for multi-digit number
      while (Serial.available() > 0) {
        char nextChar = Serial.peek();
        if (nextChar >= '0' && nextChar <= '9') {
          newSpeed = newSpeed * 10 + (Serial.read() - '0');
        } else {
          break;
        }
      }
      
      if (newSpeed >= 1 && newSpeed <= 1000) {
        currentSpeed = newSpeed;
        motorFrontRight.setSpeed(currentSpeed);
        motorFrontLeft.setSpeed(currentSpeed);
        motorBackRight.setSpeed(currentSpeed);
        motorBackLeft.setSpeed(currentSpeed);
        Serial.print("Speed set to: ");
        Serial.print(currentSpeed);
        Serial.println(" steps/sec");
      } else {
        Serial.println("Invalid speed! Enter 1-1000");
      }
    }
    
    // Movement commands
    else if (command == 'f' || command == 'b' || command == 's' || 
             command == 'l' || command == 'r' || command == 'c') {
      // Read the number following the command
      float value = 0;
      while (Serial.available() > 0) {
        char nextChar = Serial.peek();
        if (nextChar >= '0' && nextChar <= '9') {
          value = value * 10 + (Serial.read() - '0');
        } else if (nextChar == '.') {
          Serial.read(); // consume decimal point
          float decimal = 0;
          float divisor = 10;
          while (Serial.available() > 0) {
            nextChar = Serial.peek();
            if (nextChar >= '0' && nextChar <= '9') {
              decimal += (Serial.read() - '0') / divisor;
              divisor *= 10;
            } else {
              break;
            }
          }
          value += decimal;
          break;
        } else {
          break;
        }
      }
      
      // Execute command
      switch (command) {
        case 'f':
          Serial.print("Moving forward ");
          Serial.print(value);
          Serial.println(" cm");
          moveLinear(value);
          break;
        case 'b':
          Serial.print("Moving backward ");
          Serial.print(value);
          Serial.println(" cm");
          moveLinear(-value);
          break;
        case 's':
          Serial.print("Strafing right ");
          Serial.print(value);
          Serial.println(" cm");
          strafe(value);
          break;
        case 'l':
          Serial.print("Strafing left ");
          Serial.print(value);
          Serial.println(" cm");
          strafe(-value);
          break;
        case 'r':
          Serial.print("Rotating clockwise ");
          Serial.print(value);
          Serial.println(" degrees");
          rotate(value);
          break;
        case 'c':
          Serial.print("Rotating counter-clockwise ");
          Serial.print(value);
          Serial.println(" degrees");
          rotate(-value);
          break;
      }
      Serial.println("Movement complete");
    }
    
    // Stop command
    else if (command == 'x' || command == 'X') {
      stopAllMotors();
      Serial.println("All motors stopped");
    }
  }
  
  // Continuous running mode (optional - comment out if not needed)
  // Uncomment the section below if you want motors to run continuously
  
  if (motorRunning) {
    motorFrontRight.runSpeed();
    motorFrontLeft.runSpeed();
    motorBackRight.runSpeed();
    motorBackLeft.runSpeed();
  }
  
}
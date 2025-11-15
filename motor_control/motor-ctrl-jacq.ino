#include <Stepper.h>

// ===== STEPPER MOTOR PIN DEFINITIONS ===== jacques edited
// Front Right Motor (Motor 1)
#define FRONT_RIGHT_1  34
#define FRONT_RIGHT_2  35
#define FRONT_RIGHT_3  36
#define FRONT_RIGHT_4  37

// Front Left Motor (Motor 2)
#define FRONT_LEFT_1   10
#define FRONT_LEFT_2   9
#define FRONT_LEFT_3   8
#define FRONT_LEFT_4   7

// Back Right Motor (Motor 3)
#define BACK_RIGHT_1   20
#define BACK_RIGHT_2   21
#define BACK_RIGHT_3   22
#define BACK_RIGHT_4   23

// Back Left Motor (Motor 4)
#define BACK_LEFT_1    18
#define BACK_LEFT_2    17
#define BACK_LEFT_3    16
#define BACK_LEFT_4    15

// ===== CALIBRATION CONSTANTS =====
// TODO: Calibrate these values for your specific setup
const int stepsPerRevolution = 2048;
float stepsPerCm = 81.48733;           // Steps needed to move 1cm - jacques cal'd
float stepsPerDegree = 17.77778;        // Steps per motor to rotate robot 1 degree - jacques cal'd

// Wheel diameter and robot dimensions (for reference/calculation)
// You'll use these to calculate the above constants
const float wheelDiameter = 8.0;     // cm - measure your wheel diameter
const float robotWidth = 25.0;       // cm - distance between left and right wheels   jacques measured wheeltrack
const float robotLength = 16.0;      // cm - distance between front and back wheels   jacques measured wheelbase

// ===== STEPPER MOTOR INSTANCES =====
// Pins entered in sequence IN1-IN3-IN2-IN4 for proper step sequence
Stepper motorFrontRight = Stepper(stepsPerRevolution, FRONT_RIGHT_1, FRONT_RIGHT_3, FRONT_RIGHT_2, FRONT_RIGHT_4);
Stepper motorFrontLeft = Stepper(stepsPerRevolution, FRONT_LEFT_1, FRONT_LEFT_3, FRONT_LEFT_2, FRONT_LEFT_4);
Stepper motorBackRight = Stepper(stepsPerRevolution, BACK_RIGHT_1, BACK_RIGHT_3, BACK_RIGHT_2, BACK_RIGHT_4);
Stepper motorBackLeft = Stepper(stepsPerRevolution, BACK_LEFT_1, BACK_LEFT_3, BACK_LEFT_2, BACK_LEFT_4);

// ===== ADC CONFIGURATION =====
const int adcPin = 34;
const int voltageThreshold = 100;

// ===== GLOBAL VARIABLES =====
int currentSpeed = 8;
bool motorRunning = true;

// ===== CALIBRATION FUNCTIONS =====

// Move robot forward/backward by distance in cm
void moveLinear(float distanceCm) {
  int steps = (int)(distanceCm * stepsPerCm);
  
  if (motorRunning) {
    // For mecanum: all wheels rotate same direction for forward/backward
    motorFrontRight.step(steps);
    motorFrontLeft.step(steps);
    motorBackRight.step(steps);
    motorBackLeft.step(steps);
  }
}

// Strafe left/right by distance in cm
void strafe(float distanceCm) {
  int steps = (int)(distanceCm * stepsPerCm);
  
  if (motorRunning) {
    // For mecanum strafing: diagonal wheels work together
    // Right strafe: FR and BL forward, FL and BR backward
    motorFrontRight.step(steps);
    motorFrontLeft.step(-steps);
    motorBackRight.step(-steps);
    motorBackLeft.step(steps);
  }
}

// Rotate robot by theta degrees (positive = clockwise, negative = counter-clockwise)
void rotate(float thetaDegrees) {
  int steps = (int)(thetaDegrees * stepsPerDegree);
  
  if (motorRunning) {
    // For rotation: left and right sides turn opposite directions
    motorFrontRight.step(steps);
    motorFrontLeft.step(steps);
    motorBackRight.step(-steps);
    motorBackLeft.step(-steps);
  }
}

// ===== UTILITY FUNCTIONS =====

// Stop all motors
void stopAllMotors() {
  // Motors stop when no step commands are issued
  // This is more of a state flag function
  motorRunning = false;
}

// Check ADC and update motor running state
bool checkADC() {
  int adcValue = analogRead(adcPin);
  Serial.println(adcValue);
  
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

// ===== SETUP =====
void setup() {
  Serial.begin(9600);
  pinMode(adcPin, INPUT);
  
  Serial.println("=== Mecanum Wheel Robot Ready ===");
  Serial.println("Commands:");
  Serial.println("  Speed (1-16): Set motor speed");
  Serial.println("  'f10': Move forward 10cm");
  Serial.println("  's5': Strafe right 5cm");
  Serial.println("  'r90': Rotate 90 degrees");
  Serial.print("ADC threshold: ");
  Serial.println(voltageThreshold);
  Serial.println("\nCalibration needed for:");
  Serial.println("  - stepsPerCm");
  Serial.println("  - stepsPerDegree");
  
  // Set initial speed for all motors
  motorFrontRight.setSpeed(currentSpeed);
  motorFrontLeft.setSpeed(currentSpeed);
  motorBackRight.setSpeed(currentSpeed);
  motorBackLeft.setSpeed(currentSpeed);
}

// ===== MAIN LOOP =====
void loop() {
  // Check ADC (automatically updates motorRunning state)
  checkADC();
  
  // Check for serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command >= '0' && command <= '9') {
      // Speed command (number 1-16)
      int newSpeed = command - '0';
      if (Serial.available() > 0) {
        char nextChar = Serial.peek();
        if (nextChar >= '0' && nextChar <= '9') {
          newSpeed = newSpeed * 10 + (Serial.read() - '0');
        }
      }
      
      if (newSpeed >= 1 && newSpeed <= 16) {
        currentSpeed = newSpeed;
        motorFrontRight.setSpeed(currentSpeed);
        motorFrontLeft.setSpeed(currentSpeed);
        motorBackRight.setSpeed(currentSpeed);
        motorBackLeft.setSpeed(currentSpeed);
        Serial.print("Speed set to: ");
        Serial.println(currentSpeed);
      } else {
        Serial.println("Invalid speed! Enter 1-16");
      }
    }
    // You can add command parsing here for testing
    // e.g., 'f' for forward, 's' for strafe, 'r' for rotate
  }
  
  // Continuous running mode (like your original code)
  if (motorRunning) {
    motorFrontRight.step(10);
    motorFrontLeft.step(10);
    motorBackRight.step(10);
    motorBackLeft.step(10);
  }
}
// ```

// ## **Calibration Guide:**

// ### **1. Steps Per Centimeter (`stepsPerCm`):**
// ```
// stepsPerCm = stepsPerRevolution / (π * wheelDiameter)
// ```
// For 6cm diameter wheels:
// ```
// stepsPerCm = 2048 / (3.14159 * 6) ≈ 108.5 steps/cm
// ```

// **Calibration test:** 
// - Command the robot to move a known distance (e.g., 100cm)
// - Measure actual distance traveled
// - Adjust: `stepsPerCm = (stepsPerCm * commanded_distance) / actual_distance`

// ### **2. Steps Per Degree (`stepsPerDegree`):**
// For rotation, you need to account for the robot's wheelbase. The approximate formula:
// ```
// stepsPerDegree = (stepsPerRevolution * robotWidth) / (360 * wheelDiameter)

// But calibration is critical here because:

// Mecanum wheels slip during rotation
// Floor surface affects grip
// Weight distribution matters

// Calibration test:

// Command 360° rotation
// Count actual rotations
// Adjust accordingly

// Notes:

// Motor direction conventions - I assumed standard mecanum layout. If your motors spin the wrong way, add negative signs to specific motor step commands.
// The ADC check happens every loop - motors won't move if threshold is exceeded.
// I kept your continuous running mode in the loop. You'll probably want to replace this with actual movement commands once calibrated.
// Mecanum wheel directions depend on roller orientation. My functions assume:

// Front-left and back-right rollers angle one way
// Front-right and back-left angle the other way

// If your strafing goes diagonal, you need to swap some motor directions.

// Do you want me to add a command parser so you can test movements via serial commands like "f10" for forward 10cm?
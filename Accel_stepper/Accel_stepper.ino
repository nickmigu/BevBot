#include <AccelStepper.h>

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
#define BACK_LEFT_1    27
#define BACK_LEFT_2    21
#define BACK_LEFT_3    22
#define BACK_LEFT_4    23

#define DEFAULT_SPEED 400
#define MAX_SPEED     500

// ADC configuration
const int adcPin = 34;
const int voltageThreshold = 800;

// Create motor instances - pin sequence: IN1-IN3-IN2-IN4
AccelStepper motorFrontRight(AccelStepper::FULL4WIRE, FRONT_RIGHT_1, FRONT_RIGHT_3, FRONT_RIGHT_2, FRONT_RIGHT_4);
AccelStepper motorFrontLeft(AccelStepper::FULL4WIRE, FRONT_LEFT_1, FRONT_LEFT_3, FRONT_LEFT_2, FRONT_LEFT_4);
AccelStepper motorBackRight(AccelStepper::FULL4WIRE, BACK_RIGHT_1, BACK_RIGHT_3, BACK_RIGHT_2, BACK_RIGHT_4);
AccelStepper motorBackLeft(AccelStepper::FULL4WIRE, BACK_LEFT_1, BACK_LEFT_3, BACK_LEFT_2, BACK_LEFT_4);

bool motorRunning = true;

void setup() {
  Serial.begin(9600);
  pinMode(adcPin, INPUT);
  
  // Set max speed AND speed for continuous rotation
  motorFrontRight.setMaxSpeed(MAX_SPEED);
  motorFrontRight.setSpeed(DEFAULT_SPEED);
  
  motorFrontLeft.setMaxSpeed(MAX_SPEED);
  motorFrontLeft.setSpeed(DEFAULT_SPEED);
  
  motorBackRight.setMaxSpeed(MAX_SPEED);
  motorBackRight.setSpeed(DEFAULT_SPEED);
  
  motorBackLeft.setMaxSpeed(MAX_SPEED);
  motorBackLeft.setSpeed(DEFAULT_SPEED);
  
  Serial.println("Moving forward...");
}

void loop() {
  // Check ADC
  int adcValue = analogRead(adcPin);
  if (adcValue >= voltageThreshold) {
    motorRunning = false;
  } else {
    motorRunning = true;
  }
  
  // Move all motors forward concurrently
  if (motorRunning) {
    motorFrontRight.runSpeed();
    motorFrontLeft.runSpeed();
    motorBackRight.runSpeed();
    motorBackLeft.runSpeed();
  }
}
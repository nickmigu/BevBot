#include <WiFi.h>
#include <AccelStepper.h>

// ------------------------- WIFI CONFIG -------------------------
const char* ssid = "FBI Surveillance Van";
const char* password = "Idonotknow!!!";

WiFiServer server(80);
String header;

// -------------------------- STEPPER CONFIG --------------------------
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

#define DEFAULT_SPEED 400
#define MAX_SPEED     500
#define TURN_SPEED    600    // Speed for turning operations
#define TURN_ACCEL    2000    // Acceleration for turning operations

// Create motors - AccelStepper(IN1, IN3, IN2, IN4)
AccelStepper motorFR(AccelStepper::FULL4WIRE, FRONT_RIGHT_1, FRONT_RIGHT_3, FRONT_RIGHT_2, FRONT_RIGHT_4);
AccelStepper motorFL(AccelStepper::FULL4WIRE, FRONT_LEFT_1, FRONT_LEFT_3, FRONT_LEFT_2, FRONT_LEFT_4);
AccelStepper motorBR(AccelStepper::FULL4WIRE, BACK_RIGHT_1, BACK_RIGHT_3, BACK_RIGHT_2, BACK_RIGHT_4);
AccelStepper motorBL(AccelStepper::FULL4WIRE, BACK_LEFT_1, BACK_LEFT_3, BACK_LEFT_2, BACK_LEFT_4);

// ------------------------- ADC -------------------------
const int adcPin = 34;
const int voltageThreshold = 800;
bool motorRunning = true;

// ------------------------- CALIBRATION -------------------------
const int stepsPerRevolution = 2048;
float stepsPerCm = 81.48733;
float stepsPerDegree = 17.77778;  // Steps per motor to rotate robot 1 degree - jacques cal'd

// Wheel diameter and robot dimensions (for reference)
const float wheelDiameter = 8.0;   // cm
const float robotWidth = 25.0;     // cm - wheeltrack
const float robotLength = 16.0;    // cm - wheelbase
// ------------------------- PARAM PARSER -------------------------
String getValue(String data, String key) {
  int start = data.indexOf(key);
  if (start == -1) return "";
  start += key.length();
  int end = data.indexOf("&", start);
  if (end == -1) end = data.indexOf(" ", start);
  return data.substring(start, end);
}

// -------------------------  TURN TURNER -------------------------

void turnDegrees(float degrees) {
  motorFrontRight.setMaxSpeed(TURN_SPEED);
  motorFrontLeft.setMaxSpeed(TURN_SPEED);
  motorBackRight.setMaxSpeed(TURN_SPEED);
  motorBackLeft.setMaxSpeed(TURN_SPEED);
  
  motorFrontRight.setAcceleration(TURN_ACCEL);
  motorFrontLeft.setAcceleration(TURN_ACCEL);
  motorBackRight.setAcceleration(TURN_ACCEL);
  motorBackLeft.setAcceleration(TURN_ACCEL);

  long steps = (long)(abs(degrees) * stepsPerDegree);
  
  if (degrees > 0) {
    motorFrontLeft.move(steps);
    motorBackLeft.move(steps);
    motorFrontRight.move(-steps);
    motorBackRight.move(-steps);
  } else {
    motorFrontRight.move(steps);
    motorBackRight.move(steps);
    motorFrontLeft.move(-steps);
    motorBackLeft.move(-steps);
  }
  
  while (motorFrontRight.distanceToGo() != 0 || 
         motorFrontLeft.distanceToGo() != 0 ||
         motorBackRight.distanceToGo() != 0 || 
         motorBackLeft.distanceToGo() != 0) {
    motorFrontRight.run();
    motorFrontLeft.run();
    motorBackRight.run();
    motorBackLeft.run();
  }



// ------------------------- MOVEMENT HELPERS -------------------------
void runAllToTarget() {
  while (motorFR.isRunning() || motorFL.isRunning() ||
         motorBR.isRunning() || motorBL.isRunning()) {

    if (!motorRunning) return;

    motorFR.run();
    motorFL.run();
    motorBR.run();
    motorBL.run();
  }
}

void moveLinear(float cm) {
  if (!motorRunning) return;
  int steps = cm * stepsPerCm;

  motorFR.move(steps);
  motorFL.move(steps);
  motorBR.move(steps);
  motorBL.move(steps);

  runAllToTarget();
}

void moveStrafe(float cm) {
  if (!motorRunning) return;
  int steps = cm * stepsPerCm;

  motorFR.move( steps);
  motorFL.move(-steps);
  motorBR.move(-steps);
  motorBL.move( steps);

  runAllToTarget();
}

// ------------------------- SETUP -------------------------
void setup() {
  Serial.begin(115200);
  pinMode(adcPin, INPUT);

  motorFR.setMaxSpeed(MAX_SPEED);
  motorFL.setMaxSpeed(MAX_SPEED);
  motorBR.setMaxSpeed(MAX_SPEED);
  motorBL.setMaxSpeed(MAX_SPEED);

  motorFR.setSpeed(DEFAULT_SPEED);
  motorFL.setSpeed(DEFAULT_SPEED);
  motorBR.setSpeed(DEFAULT_SPEED);
  motorBL.setSpeed(DEFAULT_SPEED);

  // Connect WiFi
  Serial.println("Connecting to WiFi…");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.println(WiFi.localIP());

  server.begin();
}

// ------------------------- LOOP -------------------------
void loop() {

  // Check ADC cutoff
  int adcValue = analogRead(adcPin);
  motorRunning = adcValue < voltageThreshold;

  WiFiClient client = server.available();
  if (!client) return;

  header = "";
  String currentLine = "";

  while (client.connected()) {
    if (!client.available()) continue;

    char c = client.read();
    header += c;

    if (c != '\n') continue;

    if (currentLine.length() == 0) {

      // ===== LINEAR =====
      if (header.indexOf("GET /linear") >= 0) {
        String dir  = getValue(header, "dir=");
        int dist    = getValue(header, "dist=").toInt();

        float cm = (dir == "forward") ? dist : -dist;

        Serial.println("=== LINEAR MOVE ===");
        Serial.println(dir + " " + String(dist) + "cm");

        moveLinear(cm);
      }

      // ===== STRAFE =====
      if (header.indexOf("GET /strafe") >= 0) {
        String dir  = getValue(header, "dir=");
        int dist    = getValue(header, "dist=").toInt();

        float cm = (dir == "right") ? dist : -dist;

        Serial.println("=== STRAFE MOVE ===");
        Serial.println(dir + " " + String(dist) + "cm");

        moveStrafe(cm);
      }

      // ===== SEND WEBPAGE =====
      client.println("HTTP/1.1 200 OK");
      client.println("Content-type:text/html\n");

      client.println("<html><body style='font-family:Arial;text-align:center;'>");
      client.println("<h1>Mecanum Robot Control</h1><hr>");

      // Linear form
      client.println("<h2>Linear Move</h2>");
      client.println("<form action='/linear'>"
                     "<select name='dir'>"
                     "<option value='forward'>Forward</option>"
                     "<option value='backward'>Backward</option>"
                     "</select><br><br>"
                     "Distance (cm): <input name='dist' type='number'><br><br>"
                     "<button type='submit'>MOVE</button></form><hr>");

      // Strafe form
      client.println("<h2>Strafe Move</h2>");
      client.println("<form action='/strafe'>"
                     "<select name='dir'>"
                     "<option value='right'>Right</option>"
                     "<option value='left'>Left</option>"
                     "</select><br><br>"
                     "Distance (cm): <input name='dist' type='number'><br><br>"
                     "<button type='submit'>STRAFE</button></form>");

      client.println("</body></html>");
      break;
    }

    currentLine = "";
  }

  client.stop();
  Serial.println("Client disconnected.\n");
}

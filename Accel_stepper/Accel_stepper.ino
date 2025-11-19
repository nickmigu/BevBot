#include <WiFi.h>
#include <AccelStepper.h>

// ------------------------- WIFI CONFIG -------------------------
const char* ssid = "FBI Surveillance Van";
const char* password = "Idonotknow!!!";

WiFiServer server(80);
String header;

// -------------------------- STEPPER CONFIG --------------------------
// Front Right Motor
#define FRONT_RIGHT_1  17
#define FRONT_RIGHT_2  5
#define FRONT_RIGHT_3  18
#define FRONT_RIGHT_4  19

// Front Left Motor
#define FRONT_LEFT_1   26
#define FRONT_LEFT_2   25
#define FRONT_LEFT_3   33
#define FRONT_LEFT_4   32

// Back Right Motor
#define BACK_RIGHT_1   15
#define BACK_RIGHT_2   2
#define BACK_RIGHT_3   4
#define BACK_RIGHT_4   16

// Back Left Motor
#define BACK_LEFT_1    27
#define BACK_LEFT_2    21
#define BACK_LEFT_3    22
#define BACK_LEFT_4    23

#define DEFAULT_SPEED 400
#define MAX_SPEED     500
#define TURN_SPEED    300    // Speed for turning operations
#define TURN_ACCEL    300    // Acceleration for turning operations

#define PUMP_PIN 13

#define PUMP_DELAY 12000

#define BACKUP_DIST -20

// Create motors - AccelStepper(IN1, IN3, IN2, IN4)
AccelStepper motorFR(AccelStepper::FULL4WIRE, FRONT_RIGHT_1, FRONT_RIGHT_3, FRONT_RIGHT_2, FRONT_RIGHT_4);
AccelStepper motorFL(AccelStepper::FULL4WIRE, FRONT_LEFT_1, FRONT_LEFT_3, FRONT_LEFT_2, FRONT_LEFT_4);
AccelStepper motorBR(AccelStepper::FULL4WIRE, BACK_RIGHT_1, BACK_RIGHT_3, BACK_RIGHT_2, BACK_RIGHT_4);
AccelStepper motorBL(AccelStepper::FULL4WIRE, BACK_LEFT_1, BACK_LEFT_3, BACK_LEFT_2, BACK_LEFT_4);

// ------------------------- ADC -------------------------
const int adcPin = 34;
const int voltageThreshold = 2400;
bool motorRunning = true;


// ------------------------- CALIBRATION -------------------------
const int stepsPerRevolution = 2048;
float stepsPerCm = 81.48733;
float stepsPerDegree = 17.77778;  // Steps per motor to rotate robot 1 degree - jacques cal'd

// Wheel diameter and robot dimensions (for reference)
const float wheelDiameter = 8.0;   // cm
const float robotWidth = 25.0;     // cm - wheeltrack
const float robotLength = 16.0;    // cm - wheelbase

// ------------------------- TIMING -------------------------
unsigned long pumpMillis = 0;
unsigned long automatedMillis = 0;

// --------------- PENDING MOVEMENTS-------------------------
int pendingLinear = 0;
int pendingRotate = 0;

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

void turnDegrees(int degrees) {
  int count = 0;

  motorFR.setMaxSpeed(TURN_SPEED);
  motorFL.setMaxSpeed(TURN_SPEED);
  motorBR.setMaxSpeed(TURN_SPEED);
  motorBL.setMaxSpeed(TURN_SPEED);
  
  motorFR.setAcceleration(TURN_ACCEL);
  motorFL.setAcceleration(TURN_ACCEL);
  motorBR.setAcceleration(TURN_ACCEL);
  motorBL.setAcceleration(TURN_ACCEL);

  long steps = (long)(abs(degrees) * stepsPerDegree);
  
  if (degrees > 0) {
    motorFL.move(steps);
    motorBL.move(steps);
    motorFR.move(-steps);
    motorBR.move(-steps);
  } else {
    motorFR.move(steps);
    motorBR.move(steps);
    motorFL.move(-steps);
    motorBL.move(-steps);
  }
  
  while (motorFR.distanceToGo() != 0 || 
         motorFL.distanceToGo() != 0 ||
         motorBR.distanceToGo() != 0 || 
         motorBL.distanceToGo() != 0) {
    motorFR.run();
    motorFL.run();
    motorBR.run();
    motorBL.run();

// wait for prox sensor above threshold, wait 100ms, and get second good reading
    if (analogRead(adcPin) > voltageThreshold)
    {
      Serial.println("oh?");
      delay(100);
      if (analogRead(adcPin) > voltageThreshold)
      {
        Serial.println("THATS A CUPPPPP");
        motorFR.stop();
        motorFL.stop();
        motorBR.stop();
        motorBL.stop();
        
        digitalWrite(PUMP_PIN, HIGH);
        delay(PUMP_DELAY);
        digitalWrite(PUMP_PIN, LOW);

        delay(2000);
        
        // back up to indicate done to set backup dist in cm
        steps = BACKUP_DIST * stepsPerCm;
          motorFR.move(steps);
          motorFL.move(steps);
          motorBR.move(steps);
          motorBL.move(steps);

          while (motorFR.distanceToGo() != 0 || 
                motorFL.distanceToGo() != 0 ||
                motorBR.distanceToGo() != 0 || 
                motorBL.distanceToGo() != 0) {
            motorFR.run();
            motorFL.run();
            motorBR.run();
            motorBL.run();
          }

        Serial.println("o7");

        delay(5000);

        // you did good bud o7

        return;

        
      }
    }
    if (count % 200)
    {
      Serial.println(analogRead(adcPin));
    }
    // delay(100);
    count++;
  }
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

void moveLinear(int cm) {
  if (!motorRunning) return;
  int steps = cm * stepsPerCm;
  Serial.printf("moving %d cm\n", cm);



  motorFR.setSpeed(MAX_SPEED);f
  motorFL.setSpeed(MAX_SPEED);
  motorBR.setSpeed(MAX_SPEED);
  motorBL.setSpeed(MAX_SPEED);
  
  motorFR.setAcceleration(TURN_ACCEL);
  motorFL.setAcceleration(TURN_ACCEL);
  motorBR.setAcceleration(TURN_ACCEL);
  motorBL.setAcceleration(TURN_ACCEL);

// non blocking lines, sends command to other process to move that far
  motorFR.move(steps);
  motorFL.move(steps);
  motorBR.move(steps);
  motorBL.move(steps);

  int count = 0;
    // makes function blocking, 
    // will end loop when moved x cm and return back to main loop
    while (motorFR.distanceToGo() != 0 || 
         motorFL.distanceToGo() != 0 ||
         motorBR.distanceToGo() != 0 || 
         motorBL.distanceToGo() != 0) {

        motorFR.run();
        motorFL.run();
        motorBR.run();
        motorBL.run();

      // wait for prox sensor above threshold, wait 100ms, and get second good reading
      if (analogRead(adcPin) > voltageThreshold)
      {
        Serial.println("oh?");
        delay(100);
        if (analogRead(adcPin) > voltageThreshold)
        {
          Serial.println("THATS A CUPPPPP");
          motorFR.stop();
          motorFL.stop();
          motorBR.stop();
          motorBL.stop();
          
          digitalWrite(PUMP_PIN, HIGH);
          delay(PUMP_DELAY);
          digitalWrite(PUMP_PIN, LOW);

          delay(2000);
          
          // back up to indicate done to set backup dist in cm
          steps = BACKUP_DIST * stepsPerCm;
            motorFR.move(steps);
            motorFL.move(steps);
            motorBR.move(steps);
            motorBL.move(steps);

            while (motorFR.distanceToGo() != 0 || 
                  motorFL.distanceToGo() != 0 ||
                  motorBR.distanceToGo() != 0 || 
                  motorBL.distanceToGo() != 0) {
              motorFR.run();
              motorFL.run();
              motorBR.run();
              motorBL.run();
            }

          Serial.println("o7");

          // you did good bud o7

          while(1);

          
        }
      }
      if (count % 200)
      {
        Serial.println(analogRead(adcPin));
      }
      // delay(100);
      count++;
    }
  }

//   runAllToTarget();
// }

void moveStrafe(float cm) {
  if (!motorRunning) return;
  int steps = cm * stepsPerCm;

  motorFR.move( steps);
  motorFL.move(-steps);
  motorBR.move(-steps);
  motorBL.move( steps);

  runAllToTarget();
}

void sendResponse(WiFiClient client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-type:text/html");
  client.println("Connection: close");
  client.println();
  client.println("<html><body><h1>Command received</h1></body></html>");
  client.flush();     // <-- MAKE SURE IT LEAVES
  delay(20);          // <-- Give time to send before blocking
}

void handleWebsiteRequest(int dist, int deg) {
  if (header.indexOf("GET /linear") >= 0) {
    Serial.println("=== LINEAR MOVE ===");
    Serial.println("Straight " + String(dist) + "cm");
    pendingLinear = dist;
  }

  if (header.indexOf("GET /rotate") >= 0) {
    Serial.println("=== ROTATIONAL MOVE ===");
    Serial.println("Rotating " + String(deg) + "degrees");
    pendingRotate = deg;
  }

  if (header.indexOf("GET /pump") >= 0) {
    Serial.println("=== PUMPer ===");
    Serial.println("PUMPn for a sec");

    // set high and set current millis, reset elsewhere
    pumpMillis = millis();
    digitalWrite(PUMP_PIN, HIGH);
  } 
}

void printWebsiteInterface(WiFiClient client) {
  client.println("<html><body>");
  // Linear form
  client.println("<h2>Linear Move</h2>");
  client.println("<form action='/linear'>"
                "Distance (cm): <input name='dist' type='number'><br><br>"
                "<button type='submit'>MOVE</button></form><hr>");

  // Rotation form
  client.println("<h2>Rotate</h2>");
  client.println("<form action='/rotate'>"
                "Degrees: <input name='deg' type='number'><br><br>"
                "<button type='submit'>ROTATE</button></form>");

  // Pump button
  client.println("<h2>Pump</h2>");
  client.println("<form action='/pump'>"
                "<button type='submit'>PUMP N DUMP</button></form>");
  client.println("</body></html>");
}

// ------------------------- SETUP -------------------------
void setup() {
  Serial.begin(115200);
  pinMode(adcPin, INPUT);
  pinMode(PUMP_PIN, OUTPUT);

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
  Serial.println(analogRead(adcPin));
}

// ------------------------- LOOP -------------------------
void loop() {
  // Check ADC cutoff
  // int adcValue = analogRead(adcPin);
  // motorRunning = adcValue < voltageThreshold;

  WiFiClient client = server.available();
  if (!client) return;

  header = "";
  String currentLine = "";

  pendingLinear = 0;
  pendingRotate = 0;

  while (client.connected()) {
    // motorRunning = adcValue < voltageThreshold;

    if(millis() - pumpMillis >= PUMP_DELAY) {
      digitalWrite(PUMP_PIN, LOW);
    }
    if (!client.available()) continue;

    char c = client.read();
    header += c;

    if (c == '\n') {
      if (currentLine.length() == 0) {
        int dist = getValue(header, "dist=").toInt();
        int deg  = getValue(header, "deg=").toInt();

        // if we've received something, send a response first
        sendResponse(client);
        // run motors according to the received response
        handleWebsiteRequest(dist, deg);
        // display website
        printWebsiteInterface(client);
        
        break;
      } else {
        currentLine = "";
      }
    } else if (c != '\r') {
      currentLine += c;
    }

  }

  moveLinear(pendingLinear);
  turnDegrees(pendingRotate);

  // if client disconnects, continue to handle pump
  if(millis() - pumpMillis >= PUMP_DELAY) {
    digitalWrite(PUMP_PIN, LOW);
  }

  client.stop();
  Serial.println("Client disconnected.\n");
}

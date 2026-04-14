#include <Servo.h>

// Servo objects
Servo servoBase;          // Base
Servo servoShoulder1;     // Shoulder servo 1
Servo servoShoulder2;     // Shoulder servo 2
Servo servoElbow;         // Elbow
Servo servoWristRoll;     // Wrist roll
Servo servoWristRotate;   // Wrist rotate
Servo servoGripper;       // Gripper

// Pin assignments
const int PIN_BASE           = 3;
const int PIN_SHOULDER_1     = 4;
const int PIN_SHOULDER_2     = 5;
const int PIN_ELBOW          = 6;
const int PIN_WRIST_ROLL     = 9;
const int PIN_WRIST_ROTATE   = 10;
const int PIN_GRIPPER        = 11;

// Current servo positions
int posBase = 90;
int posShoulder = 90;
int posElbow = 90;
int posWristRoll = 90;
int posWristRotate = 90;
int posGripper = 80;

// Home position
const int HOME_BASE         = 90;
const int HOME_SHOULDER     = 70;
const int HOME_ELBOW        = 160;
const int HOME_WRIST_ROLL   = 90;
const int HOME_WRIST_ROTATE = 90;
const int HOME_GRIPPER      = 80;

// ---------------------------------
// 3 pickup zones
// Tune these first
// ---------------------------------
const int PICK_LEFT_BASE      = 60;
const int PICK_CENTER_BASE    = 90;
const int PICK_RIGHT_BASE     = 120;

const int PICK_SHOULDER       = 0;
const int PICK_ELBOW          = 150;
const int PICK_WRIST_ROLL     = 90;
const int PICK_WRIST_ROTATE   = 90;
const int PICK_GRIPPER_OPEN   = 80;
const int PICK_GRIPPER_CLOSED = 45;

// Slightly raised pickup pose after gripping
const int LIFT_SHOULDER = 105;
const int LIFT_ELBOW    = 110;

// 4 output bins
const int BIN_RED_BASE     = 35;
const int BIN_BLUE_BASE    = 145;
const int BIN_CUBE_BASE    = 35;
const int BIN_SPHERE_BASE  = 145;

// PICK_BOTH behaviour:
// true  = sort into RED / BLUE bins
// false = sort into CUBE / SPHERE bins
const bool SORT_BY_COLOUR = true;

// Serial buffer
String inputLine = "";

// Set to true if one shoulder servo is mirrored mechanically
const bool INVERT_SHOULDER_2 = false;

// ----------------------------
// Helper functions
// ----------------------------
int clampAngle(int angle) {
  if (angle < 0) return 0;
  if (angle > 180) return 180;
  return angle;
}

int shoulder2Angle(int angle) {
  if (INVERT_SHOULDER_2) {
    return 180 - angle;
  }
  return angle;
}

bool isCubeShape(String shape) {
  return (shape == "SQUARE" || shape == "RECTANGLE" || shape == "CUBE");
}

bool isSphereShape(String shape) {
  return (shape == "CIRCLE" || shape == "SPHERE");
}

bool isValidZone(String zone) {
  return (zone == "LEFT" || zone == "CENTER" || zone == "RIGHT");
}

int getPickupBaseForZone(String zone) {
  if (zone == "LEFT") return PICK_LEFT_BASE;
  if (zone == "CENTER") return PICK_CENTER_BASE;
  if (zone == "RIGHT") return PICK_RIGHT_BASE;
  return PICK_CENTER_BASE;
}

void writeAllServos() {
  servoBase.write(posBase);

  servoShoulder1.write(posShoulder);
  servoShoulder2.write(shoulder2Angle(posShoulder));

  servoElbow.write(posElbow);
  servoWristRoll.write(posWristRoll);
  servoWristRotate.write(posWristRotate);
  servoGripper.write(posGripper);
}

void moveAllSmooth(
  int targetBase,
  int targetShoulder,
  int targetElbow,
  int targetWristRoll,
  int targetWristRotate,
  int targetGripper,
  int stepDelay
) {
  targetBase = clampAngle(targetBase);
  targetShoulder = clampAngle(targetShoulder);
  targetElbow = clampAngle(targetElbow);
  targetWristRoll = clampAngle(targetWristRoll);
  targetWristRotate = clampAngle(targetWristRotate);
  targetGripper = clampAngle(targetGripper);

  bool moving = true;

  while (moving) {
    moving = false;

    if (posBase < targetBase) { posBase++; moving = true; }
    else if (posBase > targetBase) { posBase--; moving = true; }

    if (posShoulder < targetShoulder) { posShoulder++; moving = true; }
    else if (posShoulder > targetShoulder) { posShoulder--; moving = true; }

    if (posElbow < targetElbow) { posElbow++; moving = true; }
    else if (posElbow > targetElbow) { posElbow--; moving = true; }

    if (posWristRoll < targetWristRoll) { posWristRoll++; moving = true; }
    else if (posWristRoll > targetWristRoll) { posWristRoll--; moving = true; }

    if (posWristRotate < targetWristRotate) { posWristRotate++; moving = true; }
    else if (posWristRotate > targetWristRotate) { posWristRotate--; moving = true; }

    if (posGripper < targetGripper) { posGripper++; moving = true; }
    else if (posGripper > targetGripper) { posGripper--; moving = true; }

    writeAllServos();
    delay(stepDelay);
  }
}

void goHome() {
  moveAllSmooth(
    HOME_BASE,
    HOME_SHOULDER,
    HOME_ELBOW,
    HOME_WRIST_ROLL,
    HOME_WRIST_ROTATE,
    HOME_GRIPPER,
    12
  );
}

void openGripper() {
  moveAllSmooth(
    posBase,
    posShoulder,
    posElbow,
    posWristRoll,
    posWristRotate,
    PICK_GRIPPER_OPEN,
    10
  );
}

void closeGripper() {
  moveAllSmooth(
    posBase,
    posShoulder,
    posElbow,
    posWristRoll,
    posWristRotate,
    PICK_GRIPPER_CLOSED,
    10
  );
}

void moveToPickupZone(String zone) {
  int targetBase = getPickupBaseForZone(zone);

  moveAllSmooth(
    targetBase,
    PICK_SHOULDER,
    PICK_ELBOW,
    PICK_WRIST_ROLL,
    PICK_WRIST_ROTATE,
    PICK_GRIPPER_OPEN,
    12
  );
}

void liftObject() {
  moveAllSmooth(
    posBase,
    LIFT_SHOULDER,
    LIFT_ELBOW,
    posWristRoll,
    posWristRotate,
    posGripper,
    12
  );
}

void moveToDropPosition(int targetBase) {
  moveAllSmooth(
    targetBase,
    105,
    110,
    90,
    90,
    posGripper,
    12
  );

  moveAllSmooth(
    targetBase,
    120,
    95,
    90,
    90,
    posGripper,
    12
  );
}

void moveToColourBin(String colour) {
  int targetBase = HOME_BASE;

  if (colour == "RED") {
    targetBase = BIN_RED_BASE;
  } else if (colour == "BLUE") {
    targetBase = BIN_BLUE_BASE;
  } else {
    Serial.println("ERROR UNSUPPORTED_COLOUR");
    return;
  }

  moveToDropPosition(targetBase);
}

void moveToShapeBin(String shape) {
  int targetBase = HOME_BASE;

  if (isCubeShape(shape)) {
    targetBase = BIN_CUBE_BASE;
  } else if (isSphereShape(shape)) {
    targetBase = BIN_SPHERE_BASE;
  } else {
    Serial.println("ERROR UNSUPPORTED_SHAPE");
    return;
  }

  moveToDropPosition(targetBase);
}

void dropObject() {
  openGripper();
  delay(300);

  moveAllSmooth(
    posBase,
    100,
    100,
    90,
    90,
    PICK_GRIPPER_OPEN,
    12
  );
}

void pickObjectFromZone(String zone) {
  Serial.println("EVENT PICKUP_START " + zone);
  moveToPickupZone(zone);
  delay(300);
  closeGripper();
  delay(300);
  liftObject();
  delay(300);
  Serial.println("EVENT PICKED_UP " + zone);
}

// ----------------------------
// Serial command processing
// ----------------------------
void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "HOME") {
    goHome();
    Serial.println("DONE HOME");
    return;
  }

  if (cmd == "OPEN") {
    openGripper();
    Serial.println("DONE OPEN");
    return;
  }

  if (cmd == "CLOSE") {
    closeGripper();
    Serial.println("DONE CLOSE");
    return;
  }

  if (cmd == "PICK_TEST") {
    pickObjectFromZone("CENTER");
    goHome();
    Serial.println("DONE PICK_TEST");
    return;
  }

  if (cmd.startsWith("PICK_ZONE_TEST ")) {
    String zone = cmd.substring(15);
    zone.trim();

    if (!isValidZone(zone)) {
      Serial.println("ERROR UNSUPPORTED_ZONE");
      return;
    }

    moveToPickupZone(zone);
    Serial.println("DONE PICK_ZONE_TEST " + zone);
    return;
  }

  if (cmd.startsWith("PICK_COLOR_AT ")) {
    String rest = cmd.substring(14);
    rest.trim();

    int splitIndex = rest.indexOf(' ');
    if (splitIndex == -1) {
      Serial.println("ERROR BAD_PICK_COLOR_AT_FORMAT");
      return;
    }

    String colour = rest.substring(0, splitIndex);
    String zone = rest.substring(splitIndex + 1);

    colour.trim();
    zone.trim();

    if (colour != "RED" && colour != "BLUE") {
      Serial.println("ERROR UNSUPPORTED_COLOUR");
      return;
    }

    if (!isValidZone(zone)) {
      Serial.println("ERROR UNSUPPORTED_ZONE");
      return;
    }

    pickObjectFromZone(zone);
    moveToColourBin(colour);
    dropObject();
    goHome();

    Serial.println("DONE PICK_COLOR_AT " + colour + " " + zone);
    return;
  }

  if (cmd.startsWith("PICK_SHAPE_AT ")) {
    String rest = cmd.substring(14);
    rest.trim();

    int splitIndex = rest.indexOf(' ');
    if (splitIndex == -1) {
      Serial.println("ERROR BAD_PICK_SHAPE_AT_FORMAT");
      return;
    }

    String shape = rest.substring(0, splitIndex);
    String zone = rest.substring(splitIndex + 1);

    shape.trim();
    zone.trim();

    if (!isCubeShape(shape) && !isSphereShape(shape)) {
      Serial.println("ERROR UNSUPPORTED_SHAPE");
      return;
    }

    if (!isValidZone(zone)) {
      Serial.println("ERROR UNSUPPORTED_ZONE");
      return;
    }

    pickObjectFromZone(zone);
    moveToShapeBin(shape);
    dropObject();
    goHome();

    Serial.println("DONE PICK_SHAPE_AT " + shape + " " + zone);
    return;
  }

  if (cmd.startsWith("PICK_BOTH_AT ")) {
    String rest = cmd.substring(13);
    rest.trim();

    int firstSpace = rest.indexOf(' ');
    int secondSpace = rest.indexOf(' ', firstSpace + 1);

    if (firstSpace == -1 || secondSpace == -1) {
      Serial.println("ERROR BAD_PICK_BOTH_AT_FORMAT");
      return;
    }

    String colour = rest.substring(0, firstSpace);
    String shape = rest.substring(firstSpace + 1, secondSpace);
    String zone = rest.substring(secondSpace + 1);

    colour.trim();
    shape.trim();
    zone.trim();

    if (colour != "RED" && colour != "BLUE") {
      Serial.println("ERROR UNSUPPORTED_COLOUR");
      return;
    }

    if (!isCubeShape(shape) && !isSphereShape(shape)) {
      Serial.println("ERROR UNSUPPORTED_SHAPE");
      return;
    }

    if (!isValidZone(zone)) {
      Serial.println("ERROR UNSUPPORTED_ZONE");
      return;
    }

    Serial.println("COLOUR=" + colour + " SHAPE=" + shape + " ZONE=" + zone);

    pickObjectFromZone(zone);

    if (SORT_BY_COLOUR) {
      moveToColourBin(colour);
    } else {
      moveToShapeBin(shape);
    }

    dropObject();
    goHome();

    Serial.println("DONE PICK_BOTH_AT " + colour + " " + shape + " " + zone);
    return;
  }

  // old commands still supported for compatibility
  if (cmd.startsWith("PICK_COLOR ")) {
    String colour = cmd.substring(11);
    colour.trim();

    if (colour != "RED" && colour != "BLUE") {
      Serial.println("ERROR UNSUPPORTED_COLOUR");
      return;
    }

    pickObjectFromZone("CENTER");
    moveToColourBin(colour);
    dropObject();
    goHome();

    Serial.println("DONE PICK_COLOR " + colour);
    return;
  }

  if (cmd.startsWith("PICK_SHAPE ")) {
    String shape = cmd.substring(11);
    shape.trim();

    if (!isCubeShape(shape) && !isSphereShape(shape)) {
      Serial.println("ERROR UNSUPPORTED_SHAPE");
      return;
    }

    pickObjectFromZone("CENTER");
    moveToShapeBin(shape);
    dropObject();
    goHome();

    Serial.println("DONE PICK_SHAPE " + shape);
    return;
  }

  if (cmd.startsWith("PICK_BOTH ")) {
    String rest = cmd.substring(10);
    rest.trim();

    int splitIndex = rest.indexOf(' ');
    if (splitIndex == -1) {
      Serial.println("ERROR BAD_PICK_BOTH_FORMAT");
      return;
    }

    String colour = rest.substring(0, splitIndex);
    String shape = rest.substring(splitIndex + 1);

    colour.trim();
    shape.trim();

    if (colour != "RED" && colour != "BLUE") {
      Serial.println("ERROR UNSUPPORTED_COLOUR");
      return;
    }

    if (!isCubeShape(shape) && !isSphereShape(shape)) {
      Serial.println("ERROR UNSUPPORTED_SHAPE");
      return;
    }

    pickObjectFromZone("CENTER");

    if (SORT_BY_COLOUR) {
      moveToColourBin(colour);
    } else {
      moveToShapeBin(shape);
    }

    dropObject();
    goHome();

    Serial.println("DONE PICK_BOTH " + colour + " " + shape);
    return;
  }

  Serial.println("ERROR UNKNOWN_COMMAND");
}

// ----------------------------
// Setup / loop
// ----------------------------
void setup() {
  Serial.begin(115200);

  servoBase.attach(PIN_BASE);
  servoShoulder1.attach(PIN_SHOULDER_1);
  servoShoulder2.attach(PIN_SHOULDER_2);
  servoElbow.attach(PIN_ELBOW);
  servoWristRoll.attach(PIN_WRIST_ROLL);
  servoWristRotate.attach(PIN_WRIST_ROTATE);
  servoGripper.attach(PIN_GRIPPER);

  writeAllServos();
  delay(800);
  goHome();

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      processCommand(inputLine);
      inputLine = "";
    } else {
      inputLine += c;
    }
  }
}
# robotictask2

By Daniel and Ihtasham

Required Parts:
1 X Arduino Uno or Arduino Mega
1 X Raspberry Pi 5 or Pi 4
1 X WebCam
1 X Mini Breadboard
4 X MG995 or MG996R Servo
3 X MG90S Servo
1 X KCD1 Rocker Switch
1 X 608 Bearing
2 X 6203 Bearing
Various M3 Bolts (6mm, 10mm, 14mm) and Jumper Cables
5V Power Supply (Recommended: 5V 10A)

Assembly Guide
1. Prepare all components

All required components should be gathered before assembly begins. This includes the 3D printed parts, servo motors, fasteners, Arduino, Raspberry Pi, webcam, wiring, and power supply. Each component should be checked to ensure it is functional and complete.

2. Assemble the base

The base structure should be assembled first to provide a stable foundation. The base rotation servo must be mounted securely within the base so that it can rotate the entire arm smoothly.

3. Install the shoulder section

The shoulder section should be attached to the base. If two shoulder servos are used, they must be aligned correctly to ensure synchronized movement and adequate support for the arm structure.

4. Attach the elbow joint

The elbow joint should be connected to the shoulder assembly. Care must be taken to ensure the joint can move freely, as it is responsible for extending and retracting the arm.

5. Fit the wrist section

The wrist component should be installed next. This section controls the angle of the end effector and is essential for accurate positioning during object manipulation.

6. Mount the gripper

The gripper should be attached to the wrist. Its movement must be tested to ensure it can open and close effectively, allowing it to securely grasp objects.

7. Connect servos to the Arduino

Each servo motor should be connected to the appropriate pins on the Arduino. Proper wiring is essential to ensure that each joint of the arm responds correctly to control signals.

8. Set up the power supply

An external power supply should be connected to provide sufficient power to the servos and control system. This is necessary as the robot arm requires more current than a standard USB connection can supply.

9. Connect the Raspberry Pi and camera

The Raspberry Pi should be connected to the webcam. This setup enables computer vision functionality, allowing the system to detect object colour and shape.

10. Upload and test the Arduino code

The control code should be uploaded to the Arduino. Initial tests should be conducted to verify that each servo responds correctly and that predefined positions such as home, pickup, and drop-off are functioning.

11. Test individual movements

Each joint should be tested independently, including base rotation, shoulder movement, elbow articulation, wrist positioning, and gripper operation. This helps identify any mechanical or calibration issues.

12. Run the Raspberry Pi vision system

The Raspberry Pi program should be executed to enable object detection. The system should be tested to confirm that it correctly identifies objects and communicates commands to the Arduino.

13. Calibrate pickup and drop-off positions

Final adjustments should be made to the pickup zones and drop-off locations. Multiple test runs should be conducted to improve accuracy and ensure reliable sorting performance.

Arduino Test Commands in Serial Monitor:
Gripper Only
OPEN
CLOSE
OPEN
CLOSE

Pickup Zone
PICK_ZONE_TEST LEFT
PICK_ZONE_TEST CENTER
PICK_ZONE_TEST RIGHT

Pick + Grip
PICK_ZONE_CLOSE_TEST LEFT
PICK_ZONE_CLOSE_TEST CENTER
PICK_ZONE_CLOSE_TEST RIGHT

Pick + Grip + Lift
PICK_ZONE_LIFT_TEST LEFT
PICK_ZONE_LIFT_TEST CENTER
PICK_ZONE_LIFT_TEST RIGHT

Pick Up Test
PICK_TEST

Pick + Drop
PICK_TEST_DROP

Colour Bin
PICK_COLOR_AT RED LEFT
PICK_COLOR_AT RED CENTER
PICK_COLOR_AT RED RIGHT
PICK_COLOR_AT BLUE LEFT
PICK_COLOR_AT BLUE CENTER
PICK_COLOR_AT BLUE RIGHT

Shape Bin
PICK_SHAPE_AT CIRCLE LEFT
PICK_SHAPE_AT CIRCLE CENTER
PICK_SHAPE_AT CIRCLE RIGHT
PICK_SHAPE_AT RECTANGLE LEFT
PICK_SHAPE_AT RECTANGLE CENTER
PICK_SHAPE_AT RECTANGLE RIGHT

Quick Tests
HOME
OPEN
CLOSE
PICK_ZONE_TEST LEFT
PICK_ZONE_TEST CENTER
PICK_ZONE_TEST RIGHT
PICK_TEST
PICK_TEST_DROP
PICK_COLOR_AT RED CENTER
PICK_COLOR_AT BLUE CENTER
PICK_SHAPE_AT CIRCLE CENTER
PICK_SHAPE_AT RECTANGLE CENTER

Raspberry Pi Test Commands:

Press CENTER Object ID number 
Press C to Sort by Colour

Press LEFT Object ID number 
Press C to Sort by Colour

Press RIGHT Object ID number 
Press C to Sort by Colour

Press Center Object ID number 
Press P to Sort by Shape

Press LEFT Object ID number 
Press P to Sort by Shape

Press RIGHT Object ID number 
Press P to Sort by Shape

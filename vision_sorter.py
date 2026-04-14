import cv2
import numpy as np
import serial
import time

# ----------------------------
# Serial config
# Update port if needed
# Common Pi port examples:
# /dev/ttyACM0
# /dev/ttyUSB0
# ----------------------------
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

# ----------------------------
# Camera config
# ----------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ----------------------------
# Detection area thresholds
# ----------------------------
MIN_CONTOUR_AREA = 1500

# ----------------------------
# Open serial
# ----------------------------
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

# ----------------------------
# Open camera
# ----------------------------
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")


def send_command(command: str) -> None:
    print(f"[SERIAL] Sending: {command}")
    ser.write((command + "\n").encode("utf-8"))

    # Read a response if available
    response = ser.readline().decode("utf-8", errors="ignore").strip()
    if response:
        print(f"[SERIAL] Arduino: {response}")


def detect_colour(hsv_frame, contour_mask):
    """
    Detect dominant colour inside the detected object region.
    """
    masked_hsv = cv2.bitwise_and(hsv_frame, hsv_frame, mask=contour_mask)

    colour_ranges = {
        "RED": [
            ((0, 100, 80), (10, 255, 255)),
            ((170, 100, 80), (180, 255, 255)),
        ],
        "GREEN": [
            ((35, 70, 70), (85, 255, 255)),
        ],
        "BLUE": [
            ((90, 80, 70), (130, 255, 255)),
        ],
        "YELLOW": [
            ((20, 100, 100), (35, 255, 255)),
        ],
    }

    best_colour = "UNKNOWN"
    best_count = 0

    for colour_name, ranges in colour_ranges.items():
        total_count = 0
        for lower, upper in ranges:
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(masked_hsv, lower_np, upper_np)
            total_count += cv2.countNonZero(mask)

        if total_count > best_count:
            best_count = total_count
            best_colour = colour_name

    return best_colour


def detect_shape(contour):
    """
    Detect simple shape from contour polygon.
    """
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    vertices = len(approx)

    if vertices == 3:
        return "TRIANGLE"
    elif vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        if 0.9 <= aspect_ratio <= 1.1:
            return "SQUARE"
        return "RECTANGLE"
    elif vertices > 4:
        return "CIRCLE"
    else:
        return "UNKNOWN"


def get_largest_object(frame):
    """
    Returns largest valid contour and its mask.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]
    if not valid:
        return None, None

    largest = max(valid, key=cv2.contourArea)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [largest], -1, 255, thickness=cv2.FILLED)

    return largest, mask


print("Press 's' to sort detected object")
print("Press 'h' to send arm home")
print("Press 'q' to quit")

last_colour = "UNKNOWN"
last_shape = "UNKNOWN"

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    display = frame.copy()
    contour, contour_mask = get_largest_object(frame)

    if contour is not None:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        shape = detect_shape(contour)
        colour = detect_colour(hsv, contour_mask)

        last_colour = colour
        last_shape = shape

        cv2.drawContours(display, [contour], -1, (0, 255, 0), 2)

        x, y, w, h = cv2.boundingRect(contour)
        label = f"{colour} {shape}"
        cv2.putText(display, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(display, "No object detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Colour and Shape Sorting", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        if last_colour != "UNKNOWN" and last_shape != "UNKNOWN":
            # Choose one of these approaches:

            # Sort by colour only:
            # send_command(f"PICK_COLOR {last_colour}")

            # Sort by shape only:
            # send_command(f"PICK_SHAPE {last_shape}")

            # Sort using both:
            send_command(f"PICK_BOTH {last_colour} {last_shape}")
        else:
            print("No valid object detected to sort")

    elif key == ord("h"):
        send_command("HOME")

    elif key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
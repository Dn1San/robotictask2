import cv2
import numpy as np
import serial
import time
from datetime import datetime
from copy import deepcopy

# ----------------------------
# Serial config
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
# Detection thresholds
# ----------------------------
MIN_CONTOUR_AREA = 1500
MAX_SELECTABLE_OBJECTS = 9


def add_log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def connect_to_arduino():
    try:
        add_log(f"Opening serial on {SERIAL_PORT} at {BAUD_RATE} baud")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

        time.sleep(2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        add_log("Testing Arduino connection")
        ser.write(b"HOME\n")
        time.sleep(1)

        replies = []
        start_time = time.time()
        while time.time() - start_time < 2:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    replies.append(line)

        if replies:
            for reply in replies:
                add_log(f"Arduino: {reply}")
        else:
            add_log("WARNING: No reply from Arduino")

        return ser

    except Exception as e:
        raise RuntimeError(f"Failed to connect to Arduino: {e}")


def send_command(ser, command: str, detected_colour="UNKNOWN", detected_shape="UNKNOWN",
                 snapshot_label=None, pickup_zone="UNKNOWN") -> None:
    add_log(f"Sending command: {command}")

    if snapshot_label is not None:
        add_log(f"Using frozen selection: {snapshot_label}")

    if command.startswith("PICK_COLOR_AT"):
        add_log(
            f"Detected object snapshot: colour={detected_colour}, shape={detected_shape}, zone={pickup_zone}"
        )
        add_log("Pickup started")
    elif command.startswith("PICK_SHAPE_AT"):
        add_log(
            f"Detected object snapshot: colour={detected_colour}, shape={detected_shape}, zone={pickup_zone}"
        )
        add_log("Pickup started")
    elif command == "HOME":
        add_log("Moving arm home")

    ser.write((command + "\n").encode("utf-8"))
    time.sleep(0.5)

    responses = []
    start_time = time.time()
    while time.time() - start_time < 8:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                responses.append(line)
                add_log(f"Arduino: {line}")

                if "PICKED_UP" in line:
                    add_log("Pickup confirmed")
                elif "DROPPED_OFF" in line:
                    add_log("Drop-off confirmed")

    if not responses:
        add_log("No response received from Arduino")

    for response in responses:
        if response.startswith("DONE PICK_COLOR_AT"):
            add_log("Drop-off complete for colour sort")
        elif response.startswith("DONE PICK_SHAPE_AT"):
            add_log("Drop-off complete for shape sort")
        elif response.startswith("DONE HOME"):
            add_log("Arm returned home")


def get_colour_masks(hsv_frame):
    colour_ranges = {
        "RED": [
            ((0, 100, 80), (10, 255, 255)),
            ((170, 100, 80), (180, 255, 255)),
        ],
        "BLUE": [
            ((90, 80, 70), (130, 255, 255)),
        ],
    }

    kernel = np.ones((5, 5), np.uint8)
    masks = {}

    for colour_name, ranges in colour_ranges.items():
        combined_mask = None

        for lower, upper in ranges:
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv_frame, lower_np, upper_np)

            if combined_mask is None:
                combined_mask = mask
            else:
                combined_mask = cv2.bitwise_or(combined_mask, mask)

        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        masks[colour_name] = combined_mask

    return masks


def get_valid_contours_from_mask(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]


def detect_shape(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    if perimeter == 0:
        return "UNKNOWN", 0, 0.0

    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    vertices = len(approx)

    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = w / float(h)
    circularity = (4 * np.pi * area) / (perimeter * perimeter)

    if vertices == 3:
        return "TRIANGLE", vertices, circularity

    if vertices == 4:
        if 0.9 <= aspect_ratio <= 1.1:
            return "SQUARE", vertices, circularity
        return "RECTANGLE", vertices, circularity

    if circularity > 0.80:
        return "CIRCLE", vertices, circularity

    if vertices >= 5:
        return "RECTANGLE", vertices, circularity

    return "UNKNOWN", vertices, circularity


def map_shape_to_bin_shape(raw_shape: str) -> str:
    if raw_shape in ("SQUARE", "RECTANGLE"):
        return "CUBE"
    if raw_shape == "CIRCLE":
        return "SPHERE"
    return "UNKNOWN"


def get_average_hue(hsv_frame, contour):
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

    hue_channel = hsv_frame[:, :, 0]
    masked_hue = hue_channel[mask > 0]

    if masked_hue.size == 0:
        return -1.0

    return float(np.mean(masked_hue))


def get_pickup_zone(center_x: int, frame_width: int) -> str:
    third = frame_width / 3.0
    if center_x < third:
        return "LEFT"
    elif center_x < 2 * third:
        return "CENTER"
    return "RIGHT"


def detect_multiple_objects(hsv_frame):
    masks = get_colour_masks(hsv_frame)
    detections = []

    for colour_name, mask in masks.items():
        contours = get_valid_contours_from_mask(mask)

        for contour in contours:
            raw_shape, vertices, circularity = detect_shape(contour)
            bin_shape = map_shape_to_bin_shape(raw_shape)
            avg_hue = get_average_hue(hsv_frame, contour)
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            center_x = x + (w // 2)
            center_y = y + (h // 2)
            pickup_zone = get_pickup_zone(center_x, FRAME_WIDTH)

            valid_colour = colour_name in ("RED", "BLUE")
            valid_shape = bin_shape in ("CUBE", "SPHERE")

            detections.append({
                "colour": colour_name,
                "raw_shape": raw_shape,
                "bin_shape": bin_shape,
                "vertices": vertices,
                "circularity": circularity,
                "avg_hue": avg_hue,
                "area": area,
                "bbox": (x, y, w, h),
                "center": (center_x, center_y),
                "pickup_zone": pickup_zone,
                "contour": contour,
                "valid": valid_colour and valid_shape,
            })

    detections.sort(key=lambda d: d["area"], reverse=True)

    for idx, det in enumerate(detections[:MAX_SELECTABLE_OBJECTS], start=1):
        det["display_id"] = idx

    return detections[:MAX_SELECTABLE_OBJECTS]


# ----------------------------
# Connect to Arduino
# ----------------------------
ser = connect_to_arduino()

# ----------------------------
# Open camera
# ----------------------------
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

add_log("Camera opened successfully")
add_log("Controls: 1-9 select object snapshot, c=sort by colour, p=sort by shape, h=home, x=clear, q=quit")
add_log("Pickup zones: LEFT / CENTER / RIGHT")

selected_snapshot = None  # frozen object snapshot

while True:
    ret, frame = cap.read()
    if not ret:
        add_log("Failed to read frame")
        break

    display = frame.copy()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    detections = detect_multiple_objects(hsv)

    # Draw vertical zone guides
    left_boundary = FRAME_WIDTH // 3
    right_boundary = (2 * FRAME_WIDTH) // 3
    cv2.line(display, (left_boundary, 0), (left_boundary, FRAME_HEIGHT), (100, 100, 100), 1)
    cv2.line(display, (right_boundary, 0), (right_boundary, FRAME_HEIGHT), (100, 100, 100), 1)

    cv2.putText(display, "LEFT", (30, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    cv2.putText(display, "CENTER", (FRAME_WIDTH // 2 - 45, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    cv2.putText(display, "RIGHT", (FRAME_WIDTH - 90, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # Draw live detections
    for det in detections:
        x, y, w, h = det["bbox"]
        centre_x, centre_y = det["center"]
        colour = det["colour"]
        bin_shape = det["bin_shape"]
        raw_shape = det["raw_shape"]
        vertices = det["vertices"]
        circularity = det["circularity"]
        avg_hue = det["avg_hue"]
        pickup_zone = det["pickup_zone"]
        display_id = det["display_id"]

        # highlight the live detection that matches the frozen snapshot best visually
        is_selected_like = False
        if selected_snapshot is not None:
            sx, sy = selected_snapshot["center"]
            if abs(centre_x - sx) < 25 and abs(centre_y - sy) < 25:
                is_selected_like = True

        box_colour = (0, 255, 255) if is_selected_like else (0, 255, 0)

        cv2.drawContours(display, [det["contour"]], -1, box_colour, 2)
        cv2.rectangle(display, (x, y), (x + w, y + h), box_colour, 2)
        cv2.circle(display, (centre_x, centre_y), 4, box_colour, -1)

        label = f"ID:{display_id} {colour} {bin_shape}"
        debug1 = f"Zone:{pickup_zone} Raw:{raw_shape}"
        debug2 = f"V:{vertices} C:{circularity:.2f} Hue:{avg_hue:.1f}"

        cv2.putText(display, label, (x, y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, box_colour, 2)
        cv2.putText(display, debug1, (x, y + h + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 0, 0), 2)
        cv2.putText(display, debug2, (x, y + h + 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 0, 0), 2)

    if not detections:
        cv2.putText(display, "No objects detected", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    selected_text = "None"
    if selected_snapshot is not None:
        selected_text = (
            f"{selected_snapshot['colour']} "
            f"{selected_snapshot['bin_shape']} "
            f"{selected_snapshot['pickup_zone']}"
        )

    cv2.putText(display, f"Frozen selection: {selected_text}", (20, FRAME_HEIGHT - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
    cv2.putText(display, "1-9 snapshot  c=colour  p=shape  h=home  x=clear  q=quit", (20, FRAME_HEIGHT - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)

    cv2.imshow("Colour and Shape Sorting", display)
    key = cv2.waitKey(1) & 0xFF

    # Freeze current detection as snapshot
    if ord("1") <= key <= ord("9"):
        requested_id = key - ord("0")
        chosen = next((d for d in detections if d["display_id"] == requested_id), None)

        if chosen is not None:
            selected_snapshot = {
                "display_id": chosen["display_id"],
                "colour": chosen["colour"],
                "raw_shape": chosen["raw_shape"],
                "bin_shape": chosen["bin_shape"],
                "pickup_zone": chosen["pickup_zone"],
                "center": chosen["center"],
                "bbox": chosen["bbox"],
                "valid": chosen["valid"],
            }

            add_log(
                f"Frozen selection from live ID {requested_id}: "
                f"{selected_snapshot['colour']} {selected_snapshot['bin_shape']} "
                f"(raw={selected_snapshot['raw_shape']}, zone={selected_snapshot['pickup_zone']})"
            )
        else:
            add_log(f"No object with live ID {requested_id}")

    elif key == ord("x"):
        selected_snapshot = None
        add_log("Cleared frozen selection")

    elif key == ord("c"):
        if selected_snapshot is not None and selected_snapshot["valid"]:
            send_command(
                ser,
                f"PICK_COLOR_AT {selected_snapshot['colour']} {selected_snapshot['pickup_zone']}",
                detected_colour=selected_snapshot["colour"],
                detected_shape=selected_snapshot["bin_shape"],
                snapshot_label=f"ID {selected_snapshot['display_id']}",
                pickup_zone=selected_snapshot["pickup_zone"]
            )
        else:
            add_log("No valid frozen selection to sort by colour")

    elif key == ord("p"):
        if selected_snapshot is not None and selected_snapshot["valid"]:
            send_command(
                ser,
                f"PICK_SHAPE_AT {selected_snapshot['raw_shape']} {selected_snapshot['pickup_zone']}",
                detected_colour=selected_snapshot["colour"],
                detected_shape=selected_snapshot["bin_shape"],
                snapshot_label=f"ID {selected_snapshot['display_id']}",
                pickup_zone=selected_snapshot["pickup_zone"]
            )
        else:
            add_log("No valid frozen selection to sort by shape")

    elif key == ord("h"):
        send_command(ser, "HOME")

    elif key == ord("q"):
        add_log("Quitting program")
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
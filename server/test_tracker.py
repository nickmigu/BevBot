import cv2
import numpy as np
import requests
import json
import os
from time import sleep, time
from cup_detector import detect_red_cup
from display_utils import prepare_display_frame, draw_detection_overlay, update_and_draw_fps
from esp32_control import calculate_movement, send_command_to_esp32

# IP Webcam stream URL
# STREAM_URL = "http://192.168.1.160:8080/video"
STREAM_URL = "http://192.168.1.85:8080/video"
# Alternative: Use snapshot mode for lower bandwidth
# SNAPSHOT_URL = "http://192.168.1.85:8080/shot.jpg"

# Display window size parameters
WINDOW_WIDTH = 640   # Adjust this to make window wider/narrower
WINDOW_HEIGHT = 480  # Adjust this to make window taller/shorter

# Processing scale (0.0 to 1.0) - lower = faster, higher = more accurate
# 1.0 = full resolution, 0.5 = half resolution, 0.25 = quarter resolution
PROCESS_SCALE = 0.4  # Recommended: 0.2-0.4 for good speed/accuracy balance

# Flip video upside down (useful if camera is mounted upside down)
FLIP_VIDEO = False  # Set to True to rotate video 180 degrees

# Camera field of view (in degrees)
CAMERA_FOV = 120  # Typical phone camera horizontal FOV (adjust for your camera)
# 120 FOV Jacques Phone Ultra Wide
ANGLE_DEADZONE = 2.0  # Angles within ±2° are considered centered

# HSV Color range for red cup detection
# These values are loaded from hsv_config.json (use calibrate_hsv.py to adjust)
# Config file path
CONFIG_FILE = "hsv_config.json"

# Default HSV values (fallback if config file doesn't exist)
DEFAULT_HSV = {
    "red_lower_1": [0, 100, 100],
    "red_upper_1": [10, 255, 255],
    "red_lower_2": [160, 100, 100],
    "red_upper_2": [180, 255, 255]
}

def load_hsv_config():
    """Load HSV values from config file or use defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                print(f"✓ Loaded HSV config from {CONFIG_FILE}")
                return config
        except Exception as e:
            print(f"⚠ Error loading config: {e}")
            print(f"Using default HSV values")
            return DEFAULT_HSV.copy()
    else:
        print(f"⚠ Config file not found: {CONFIG_FILE}")
        print(f"Using default HSV values (run calibrate_hsv.py to create config)")
        return DEFAULT_HSV.copy()

# Load HSV configuration
hsv_config = load_hsv_config()

def capture_frame(cap):
    """
    Capture frame from video stream
    Returns: frame (or None if failed)
    """
    if cap is not None:
        ret, frame = cap.read()
        if not ret:
            print("Failed to get frame")
            sleep(1)
            return None
    else:
        # Snapshot mode (less resource intensive)
        img_resp = requests.get(SNAPSHOT_URL)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)
    return frame

def should_exit():
    """
    Check if user wants to exit (q key or window closed)
    Returns: True if should exit, False otherwise
    """
    # Check for 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return True

    # Check if window was closed
    if cv2.getWindowProperty('Robot Vision', cv2.WND_PROP_VISIBLE) < 1:
        return True

    return False

def main():
    # Open video stream
    cap = cv2.VideoCapture(STREAM_URL)

    # Optimize video capture settings for speed
    if cap is not None:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame

    print("Starting red cup tracker...")

    # Initialize FPS tracker
    fps_tracker = {
        'fps': 0,
        'frame_count': 0,
        'start_time': time()
    }

    while True:
        # Capture frame from camera
        frame = capture_frame(cap)
        if frame is None:
            continue

        # Flip video if needed (camera mounted upside down)
        if FLIP_VIDEO:
            frame = cv2.flip(frame, -1)  # -1 flips both horizontally and vertically (180 degree rotation)

        # Calculate processing dimensions and resize frame
        orig_height, orig_width = frame.shape[:2]
        process_width = int(orig_width * PROCESS_SCALE)
        process_height = int(orig_height * PROCESS_SCALE)
        process_frame = cv2.resize(frame, (process_width, process_height))
        height, width = process_frame.shape[:2]

        # Detect red cup on processed frame (using improved detector from cup_detector.py)
        found, cx, cy, area, bbox, confidence, _ = detect_red_cup(process_frame, hsv_config)

        # Calculate turn angle and send command to robot
        if found:
            angle = calculate_movement(cx, cy, width, height, CAMERA_FOV, ANGLE_DEADZONE)
            send_command_to_esp32("MOVE", angle)
        else:
            angle = 0
            send_command_to_esp32("STOP", 0)

        # Prepare display frame and calculate scale factors
        display_frame, scale_x, scale_y = prepare_display_frame(process_frame, width, height, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw detection visualization (with confidence score)
        draw_detection_overlay(display_frame, found, angle, area, bbox, cx, cy, scale_x, scale_y, confidence)

        # Update and draw FPS counter
        fps_tracker = update_and_draw_fps(display_frame, fps_tracker, WINDOW_HEIGHT)

        # Show frame
        cv2.imshow('Robot Vision', display_frame)

        # Check for exit
        if should_exit():
            break

    # Cleanup
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
"""
Centralized configuration for BevBot tracking system
All shared constants and configuration loading/saving
"""
import json
import os

# IP Webcam stream URL
STREAM_URL = "http://192.168.1.85:8080/video"

# ESP32 microcontroller IP address
ESP32_IP = "http://192.168.1.200"
# ESP32_IP = "temp"

# Debug mode: Use local webcam instead of network stream
# Set to True to use local USB/built-in webcam (useful for testing)
# Set to False to use network IP Webcam stream (production mode)
DEBUG_MODE = False
LOCAL_CAMERA_INDEX = 0  # Camera device index (0 = default webcam)


# Display window size parameters
WINDOW_WIDTH = 640   # Adjust this to make window wider/narrower
WINDOW_HEIGHT = 480  # Adjust this to make window taller/shorter

# Processing scale (0.0 to 1.0) - lower = faster, higher = more accurate
# 1.0 = full resolution, 0.5 = half resolution, 0.25 = quarter resolution
PROCESS_SCALE = 0.2  # Recommended: 0.2-0.4 for good speed/accuracy balance

# Flip video upside down (useful if camera is mounted upside down)
FLIP_VIDEO = True  # Set to True to rotate video 180 degrees

# Camera field of view (in degrees)
# CAMERA_FOV = 120  # Typical phone camera horizontal FOV (adjust for your camera)
CAMERA_FOV = 60 # Nick Phone FOV
# 120 FOV Jacques Phone Ultra Wide

ANGLE_DEADZONE = 2.0  # Angles within ±2° are considered centered

# Simple control parameters
SEARCH_SPIN_ANGLE = 5  # Degrees to rotate when searching for cups (positive = right)

STEP_MOVE_DISTANCE = 10  # cm to move forward when cup is centered

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

def load_hsv_config(config_file=None):
    """Load HSV values from config file or use defaults"""
    if config_file is None:
        config_file = CONFIG_FILE

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"[OK] Loaded HSV config from {config_file}")
                return config
        except Exception as e:
            print(f"[WARNING] Error loading config: {e}")
            print(f"Using default HSV values")
            return DEFAULT_HSV.copy()
    else:
        print(f"[WARNING] Config file not found: {config_file}")
        print(f"Using default HSV values (run calibrate_hsv.py to create config)")
        return DEFAULT_HSV.copy()

def save_hsv_config(config, config_file=None):
    """Save HSV ranges to config file"""
    if config_file is None:
        config_file = CONFIG_FILE

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"[OK] Saved HSV config to {config_file}")

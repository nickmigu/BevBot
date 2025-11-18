import requests

# ESP32 IP (you'll set this up later)
ESP32_URL = "http://192.168.1.100"  # Change to your ESP32's IP

def calculate_movement(cx, cy, frame_width, frame_height, camera_fov, angle_deadzone):
    """
    Calculate robot turn angle based on cup position
    Returns: angle in degrees (negative = turn left, positive = turn right, 0 = centered)
    """
    center_x = frame_width // 2

    # Calculate horizontal offset in pixels
    offset_x = cx - center_x

    # Calculate offset as ratio of half-frame width (-1.0 to 1.0)
    offset_ratio = offset_x / (frame_width / 2)

    # Convert to angle using camera field of view
    angle = offset_ratio * (camera_fov / 2)

    # Apply deadzone - if within threshold, return 0 (centered)
    if abs(angle) < angle_deadzone:
        return 0.0

    return round(angle, 1)  # Round to 1 decimal place

def send_command_to_esp32(command, angle, esp32_url=None):
    """
    Send movement command to ESP32
    command: "MOVE" or "STOP"
    angle: turn angle in degrees (negative = left, positive = right)
    esp32_url: optional custom ESP32 URL (defaults to ESP32_URL)
    """
    url = esp32_url if esp32_url else ESP32_URL
    print(f"Command to ESP32: {command}, Angle={angle:+.1f}°")
    # try:
    #     # Adjust this based on your ESP32 API
    #     response = requests.get(f"{url}/move?cmd={command}&angle={angle}", timeout=0.5)
    #     return response.status_code == 200
    # except:
    #     return False

import requests
from config import ESP32_IP


# ============================================================================
# CONTROLS CLASS - Static interface for robot movement
# ============================================================================

class Controls:
    """
    Static class for controlling robot movement.

    Usage:
        Controls.move(10)      # Move forward 10 cm
        Controls.rotate(45)    # Rotate 45 degrees
    """

    @staticmethod
    def move(cm):
        """
        Move the robot forward/backward by specified distance.

        Args:
            cm (float): Distance in centimeters (positive = forward, negative = backward)
        """
        url = f"{ESP32_IP}/linear?dist={cm}"
        print(f"Sending linear move: {cm} cm")
        response = requests.get(url, timeout=2)
        # print("Response:", response.status_code, response.text)

    @staticmethod
    def rotate(deg):
        """
        Rotate the robot by specified angle.

        Args:
            deg (float): Angle in degrees (positive = clockwise, negative = counterclockwise)
        """
        url = f"{ESP32_IP}/rotate?deg={deg}"
        print(f"Sending rotation: {deg} degrees")
        response = requests.get(url, timeout=2)
        # print("Response:", response.status_code, response.text)
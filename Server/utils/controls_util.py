import requests
import threading
import time
from config import ESP32_IP


# ============================================================================
# CONTROLS CLASS - Static interface for robot movement
# ============================================================================

class Controls:
    """
    Static class for controlling robot movement.

    Uses a single-threaded queue that only keeps the MOST RECENT command.
    Old pending commands are discarded, ensuring the ESP32 only receives
    the latest command when it's ready.

    Usage:
        Controls.move(10)      # Move forward 10 cm (non-blocking)
        Controls.rotate(45)    # Rotate 45 degrees (non-blocking)
    """

    _lock = threading.Lock()
    _pending_command = None  # Stores (url, description) of most recent command
    _worker_thread = None
    _running = True

    @staticmethod
    def _worker():
        """
        Background worker thread that processes commands one at a time.
        Always uses the most recent command, discarding older ones.
        """
        while Controls._running:
            command_to_send = None

            # Get the latest pending command
            with Controls._lock:
                if Controls._pending_command is not None:
                    command_to_send = Controls._pending_command
                    Controls._pending_command = None  # Clear it

            # Send the command if we have one
            if command_to_send:
                url, description = command_to_send
                try:
                    response = requests.get(url, timeout=5)
                    # Uncomment for debugging:
                    # print(f"{description} - Response: {response.status_code}")
                except requests.exceptions.Timeout:
                    print(f"{description} - Timeout after 5 seconds")
                except Exception as e:
                    print(f"{description} - Error: {e}")
            else:
                # No command pending, sleep briefly to avoid busy-waiting
                time.sleep(0.01)

    @staticmethod
    def _ensure_worker_running():
        """Ensure the worker thread is started."""
        with Controls._lock:
            if Controls._worker_thread is None or not Controls._worker_thread.is_alive():
                Controls._worker_thread = threading.Thread(
                    target=Controls._worker,
                    daemon=True
                )
                Controls._worker_thread.start()

    @staticmethod
    def move(cm):
        """
        Move the robot forward/backward by specified distance.
        Returns immediately. Only the most recent command is sent when ESP32 is ready.

        Args:
            cm (float): Distance in centimeters (positive = forward, negative = backward)
        """
        Controls._ensure_worker_running()

        url = f"{ESP32_IP}/linear?dist={cm}"
        with Controls._lock:
            Controls._pending_command = (url, f"Linear move {cm} cm")
        print(f"Queued linear move: {cm} cm")

    @staticmethod
    def rotate(deg):
        """
        Rotate the robot by specified angle.
        Returns immediately. Only the most recent command is sent when ESP32 is ready.

        Args:
            deg (float): Angle in degrees (positive = clockwise, negative = counterclockwise)
        """
        Controls._ensure_worker_running()

        url = f"{ESP32_IP}/rotate?deg={deg}"
        with Controls._lock:
            Controls._pending_command = (url, f"Rotation {deg} degrees")
        print(f"Queued rotation: {deg} degrees")
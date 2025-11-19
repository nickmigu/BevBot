"""
Camera and video frame utilities
Shared functions for capturing and preprocessing video frames
"""
import cv2
import numpy as np
from time import sleep

def capture_frame(cap):
    """
    Capture frame from video stream

    Args:
        cap: cv2.VideoCapture object

    Returns:
        frame (or None if failed)
    """
    ret, frame = cap.read()
    if not ret:
        print("Failed to get frame")
        sleep(1)
        return None

    return frame

def preprocess_frame(frame, process_scale=1.0, flip_video=False):
    """
    Preprocess frame: flip and/or resize

    Args:
        frame: Input BGR frame
        process_scale: Scale factor (0.0 to 1.0)
        flip_video: Whether to flip frame 180 degrees

    Returns:
        Processed frame
    """
    if frame is None:
        return None

    # Flip video if needed (camera mounted upside down)
    if flip_video:
        frame = cv2.flip(frame, -1)  # -1 flips both horizontally and vertically (180 degree rotation)

    # Resize if scale is not 1.0
    if process_scale != 1.0:
        height, width = frame.shape[:2]
        new_width = int(width * process_scale)
        new_height = int(height * process_scale)
        frame = cv2.resize(frame, (new_width, new_height))

    return frame

def should_exit(window_name='Robot Vision'):
    """
    Check if user wants to exit (q key or window closed)

    Args:
        window_name: Name of the window to check

    Returns:
        True if should exit, False otherwise
    """
    # Check for 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return True

    # Check if window was closed
    try:
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            return True
    except:
        # Window doesn't exist
        return True

    return False

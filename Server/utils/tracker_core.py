"""
Core tracking logic - High-level API for cup tracking and movement
This module provides a clean interface that other scripts can import
"""
import cv2
from time import time
from config import (
    STREAM_URL, PROCESS_SCALE, FLIP_VIDEO, CAMERA_FOV, ANGLE_DEADZONE,
    DEBUG_MODE, LOCAL_CAMERA_INDEX, load_hsv_config
)
from utils.capture_util import capture_frame, preprocess_frame
from utils.cup_detector import detect_red_cup


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


class CupTracker:
    """
    High-level cup tracking and robot control interface

    Example usage:
        tracker = CupTracker()
        while True:
            result = tracker.update()
            if result:
                print(f"Cup at angle {result['angle']}")
            if tracker.should_exit():
                break
        tracker.cleanup()
    """

    def __init__(self, stream_url=None, process_scale=None, flip_video=None,
                 camera_fov=None, angle_deadzone=None, hsv_config=None):
        """
        Initialize cup tracker

        Args:
            stream_url: Video stream URL (defaults to config.STREAM_URL)
            process_scale: Processing scale 0.0-1.0 (defaults to config.PROCESS_SCALE)
            flip_video: Whether to flip video (defaults to config.FLIP_VIDEO)
            camera_fov: Camera field of view in degrees (defaults to config.CAMERA_FOV)
            angle_deadzone: Angle deadzone in degrees (defaults to config.ANGLE_DEADZONE)
            hsv_config: HSV configuration dict (defaults to loading from file)
        """
        # Use config defaults if not provided
        self.stream_url = stream_url if stream_url is not None else STREAM_URL
        self.process_scale = process_scale if process_scale is not None else PROCESS_SCALE
        self.flip_video = flip_video if flip_video is not None else FLIP_VIDEO
        self.camera_fov = camera_fov if camera_fov is not None else CAMERA_FOV
        self.angle_deadzone = angle_deadzone if angle_deadzone is not None else ANGLE_DEADZONE

        # Load HSV configuration
        self.hsv_config = hsv_config if hsv_config is not None else load_hsv_config()

        # Initialize video capture
        # Select camera source based on DEBUG_MODE
        if DEBUG_MODE:
            camera_source = LOCAL_CAMERA_INDEX
            print(f"DEBUG MODE: Using local webcam (device {LOCAL_CAMERA_INDEX})")
        else:
            camera_source = self.stream_url
            print(f"PRODUCTION MODE: Using network stream ({self.stream_url})")

        self.cap = cv2.VideoCapture(camera_source)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame

        # Tracking state
        self.last_frame = None
        self.last_detection = None

    def update(self):
        # return
        """
        Update tracking: capture frame, detect cup, calculate movement, send command

        Returns:
            dict or None: Tracking result with keys:
                - 'found': bool
                - 'frame': processed frame
                - 'cx', 'cy': center coordinates
                - 'area': detection area
                - 'bbox': bounding box (x, y, w, h)
                - 'confidence': detection confidence
                - 'angle': calculated turn angle
                Returns None if frame capture failed
        """
        # Capture frame
        frame = capture_frame(self.cap)
        if frame is None:
            return None

        # Preprocess frame
        process_frame = preprocess_frame(frame, self.process_scale, self.flip_video)
        if process_frame is None:
            return None

        # Store for external access
        self.last_frame = process_frame
        height, width = process_frame.shape[:2]

        # Detect red cup
        found, cx, cy, area, bbox, confidence, _ = detect_red_cup(process_frame, self.hsv_config)

        # Calculate turn angle (control handled by caller)
        if found:
            angle = calculate_movement(cx, cy, width, height, self.camera_fov, self.angle_deadzone)
        else:
            angle = 0

        # Build result
        result = {
            'found': found,
            'frame': process_frame,
            'cx': cx,
            'cy': cy,
            'area': area,
            'bbox': bbox,
            'confidence': confidence,
            'angle': angle
        }

        # Store for external access
        self.last_detection = result

        return result

    def get_last_frame(self):
        """Get the last captured/processed frame"""
        return self.last_frame

    def get_last_detection(self):
        """Get the last detection result"""
        return self.last_detection

    def cleanup(self):
        """Release resources"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()


# def track_cup_and_move(stream_url=None, process_scale=None, **kwargs):
#     """
#     Simple function interface for single-frame tracking

#     Args:
#         stream_url: Video stream URL
#         process_scale: Processing scale
#         **kwargs: Additional parameters for CupTracker

#     Returns:
#         dict: Tracking result (same as CupTracker.update())
#     """
#     tracker = CupTracker(stream_url=stream_url, process_scale=process_scale, **kwargs)
#     result = tracker.update()
#     tracker.cleanup()
#     return result

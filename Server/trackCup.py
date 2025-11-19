"""
Main tracking script - Simple interface using tracker_core module
All configuration and logic is now in modular components
"""
import cv2
import requests
from time import time
from config import WINDOW_WIDTH, WINDOW_HEIGHT, SEARCH_SPIN_ANGLE, STEP_MOVE_DISTANCE, ANGLE_DEADZONE, FIN_STEP_MOVE_DISTANCE
from utils.tracker_core import CupTracker
from utils.display_util import prepare_display_frame, draw_detection_overlay, update_and_draw_fps
from utils.capture_util import should_exit
from utils.controls_util import Controls

def display_tracking_ui(result, fps_tracker):
    """
    Handle all UI/display operations

    Args:
        result (dict): Tracking result from tracker.update()
        fps_tracker (dict): FPS tracking state

    Returns:
        dict: Updated fps_tracker
    """
    # Extract frame and detection data
    process_frame = result['frame']
    found = result['found']
    angle = result['angle']
    area = result['area']
    bbox = result['bbox']
    cx = result['cx']
    cy = result['cy']
    confidence = result['confidence']

    # Get frame dimensions
    height, width = process_frame.shape[:2]

    # Prepare display frame and calculate scale factors
    display_frame, scale_x, scale_y = prepare_display_frame(
        process_frame, width, height, WINDOW_WIDTH, WINDOW_HEIGHT
    )

    # Draw detection visualization (with confidence score)
    draw_detection_overlay(
        display_frame, found, angle, area, bbox, cx, cy,
        scale_x, scale_y, confidence
    )

    # Update and draw FPS counter
    fps_tracker = update_and_draw_fps(display_frame, fps_tracker, WINDOW_HEIGHT)

    # Show frame
    cv2.imshow('Robot Vision', display_frame)

    return fps_tracker


def main():
    """Main tracking loop with control logic"""
    print("Starting red cup tracker...")

    # Initialize tracker using modular components
    tracker = CupTracker()

    # Initialize FPS tracker
    fps_tracker = {
        'fps': 0,
        'frame_count': 0,
        'start_time': time()
    }

    while True:
        # Update tracking (capture, detect, calculate)
        result = tracker.update()

        if result is None:
            continue

        # ===== BEVBOT CONTROL LOGIC =====
        found = result['found']
        angle = result['angle']
        cy = result['cy']
        frame_height = result['frame'].shape[0]

        if found:
            print("Found CUP")
            # Cup detected - send control commands with error handling
            try:
                print(f"Angle to cup: {angle} degrees")
                if angle == 0.0:
                    # Check if cup is in bottom half of screen (close to robot)
                    if cy > frame_height * 0.3:
                        Controls.move(FIN_STEP_MOVE_DISTANCE)
                    else:
                        # Cup is centered - move forward
                        Controls.move(STEP_MOVE_DISTANCE)
                else:
                    # Cup is off-center - rotate to center it
                    Controls.rotate(angle)
            except requests.exceptions.RequestException as e:
                print(f"[WARNING] ESP32 not responding: {e}")
        else:
            print("Searching for CUP...")
            # Cup not detected - rotate to search
            try:
                Controls.rotate(SEARCH_SPIN_ANGLE)
            except requests.exceptions.RequestException as e:
                print(f"[WARNING] ESP32 not responding: {e}")

        # ===== DISPLAY UI =====
        fps_tracker = display_tracking_ui(result, fps_tracker)

        # Check for exit
        if should_exit('Robot Vision'):
            break

    # Cleanup
    tracker.cleanup()


if __name__ == "__main__":
    main()

import cv2
from time import time

def prepare_display_frame(process_frame, width, height, window_width, window_height):
    """
    Resize process frame to display size and calculate scale factors
    Returns: (display_frame, scale_x, scale_y)
    """
    display_frame = cv2.resize(process_frame, (window_width, window_height))
    scale_x = window_width / width
    scale_y = window_height / height
    return display_frame, scale_x, scale_y

def draw_detection_overlay(display_frame, found, angle, area, bbox, cx, cy, scale_x, scale_y, confidence=0.0):
    """
    Draw detection visualization on display frame
    """
    if found:
        # Scale and draw detection box
        if bbox:
            x, y, w, h = bbox
            dx = int(x * scale_x)
            dy = int(y * scale_y)
            dw = int(w * scale_x)
            dh = int(h * scale_y)
            dcx = int(cx * scale_x)
            dcy = int(cy * scale_y)

            # Color based on confidence: green = good (>75%), yellow = ok (60-75%)
            color = (0, 255, 0) if confidence >= 0.75 else (0, 255, 255)
            cv2.rectangle(display_frame, (dx, dy), (dx + dw, dy + dh), color, 2)
            cv2.circle(display_frame, (dcx, dcy), 5, (255, 0, 0), -1)

        # Draw angle and area info
        angle_text = f"Angle: {angle:+.1f}" if angle != 0 else "Angle: 0.0 (CENTERED)"
        cv2.putText(display_frame, angle_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Confidence: {confidence*100:.0f}%", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Area: {int(area)}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        # No cup detected
        cv2.putText(display_frame, "No cup", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

def update_and_draw_fps(display_frame, fps_tracker, window_height):
    """
    Update FPS counter and draw on display frame
    Returns: updated fps_tracker
    """
    fps_tracker['frame_count'] += 1

    if time() - fps_tracker['start_time'] >= 1.0:
        fps_tracker['fps'] = fps_tracker['frame_count']
        fps_tracker['frame_count'] = 0
        fps_tracker['start_time'] = time()

    cv2.putText(display_frame, f"FPS: {fps_tracker['fps']}", (10, window_height - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    return fps_tracker

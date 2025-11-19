# -*- coding: utf-8 -*-
"""
Shared Red Cup Detection Module
Used by both calibration and tracking scripts
Improved version with multi-candidate scoring and color verification
"""
import cv2
import numpy as np


def verify_color_confidence(frame, hsv, mask, bbox):
    """
    Verify that the detected region actually contains red pixels

    Args:
        frame: BGR image frame
        hsv: HSV converted frame
        mask: Binary mask from color detection
        bbox: Bounding box (x, y, w, h)

    Returns:
        float: Color confidence score (0.0 to 1.0)
    """
    x, y, w, h = bbox

    # Extract the region of interest from the mask
    roi_mask = mask[y:y+h, x:x+w]

    # Calculate percentage of red pixels in the detected region
    total_pixels = w * h
    red_pixels = np.count_nonzero(roi_mask)

    confidence = red_pixels / total_pixels if total_pixels > 0 else 0.0

    return confidence


def score_candidate(contour, frame_shape, color_confidence, area):
    """
    Score a detection candidate based on multiple criteria

    Args:
        contour: OpenCV contour
        frame_shape: Frame dimensions (height, width)
        color_confidence: Color verification score (0.0-1.0)
        area: Contour area in pixels

    Returns:
        float: Total score (higher is better)
    """
    height, width = frame_shape[:2]

    # Get bounding box
    x, y, w, h = cv2.boundingRect(contour)
    cx = x + w // 2
    cy = y + h // 2

    # Score 1: Color confidence (0.0-1.0) - Most important
    # Require at least 60% red pixels to be valid
    if color_confidence < 0.60:
        return 0.0  # Reject if not enough red pixels

    color_score = color_confidence

    # Score 2: Size score (prefer medium-sized objects)
    # Typical cup at various distances: 1000-10000 pixels
    ideal_min = 1000
    ideal_max = 10000

    if ideal_min <= area <= ideal_max:
        size_score = 1.0
    elif area < ideal_min:
        # Too small - penalize based on how small
        size_score = max(0.3, area / ideal_min)
    else:
        # Too large - penalize based on how large
        size_score = max(0.2, ideal_max / area)

    # Score 3: Position score (slight preference for lower half/center)
    # Cups are usually on tables, not high up
    vertical_position = cy / height  # 0.0 = top, 1.0 = bottom
    horizontal_center = abs(cx - width/2) / (width/2)  # 0.0 = center, 1.0 = edge

    # Prefer lower half (0.3-0.8 vertical range)
    if 0.3 <= vertical_position <= 0.8:
        position_score = 1.0
    else:
        position_score = 0.7

    # Slightly prefer center
    position_score *= (1.0 - horizontal_center * 0.2)

    # Combined score with weights
    total_score = (color_score * 0.5 +     # 50% weight on color match
                   size_score * 0.3 +       # 30% weight on size
                   position_score * 0.2)    # 20% weight on position

    return total_score


def detect_red_cup(frame, hsv_ranges, min_confidence=0.60, return_all_candidates=False):
    """
    Detect red solo cup using color detection with multi-candidate scoring

    Args:
        frame: BGR image frame
        hsv_ranges: Dictionary with keys 'red_lower_1', 'red_upper_1', 'red_lower_2', 'red_upper_2'
        min_confidence: Minimum color confidence required (0.0-1.0), default 0.60
        return_all_candidates: If True, return top 3 candidates, otherwise just best

    Returns:
        tuple: (found, center_x, center_y, area, bounding_box, confidence, candidates)
            - found: Boolean indicating if cup was detected
            - center_x: X coordinate of cup center
            - center_y: Y coordinate of cup center
            - area: Area of detected cup in pixels
            - bounding_box: Tuple (x, y, width, height) or None
            - confidence: Color confidence score (0.0-1.0)
            - candidates: List of rejected candidates (if return_all_candidates=True)
    """
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red color range - uses dual ranges from config
    RED_LOWER_1 = hsv_ranges.get('red_lower_1', [0, 100, 100])
    RED_UPPER_1 = hsv_ranges.get('red_upper_1', [10, 255, 255])
    RED_LOWER_2 = hsv_ranges.get('red_lower_2', [160, 100, 100])
    RED_UPPER_2 = hsv_ranges.get('red_upper_2', [180, 255, 255])

    mask1 = cv2.inRange(hsv, np.array(RED_LOWER_1), np.array(RED_UPPER_1))
    mask2 = cv2.inRange(hsv, np.array(RED_LOWER_2), np.array(RED_UPPER_2))
    mask = mask1 | mask2  # Fast bitwise OR

    # Single morphology operation for speed
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return False, 0, 0, 0, None, 0.0, []

    # Filter by minimum area and score all candidates
    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        # Filter noise (area > 500 pixels - increased from 200)
        if area > 500:
            x, y, w, h = cv2.boundingRect(contour)

            # Verify color confidence
            color_confidence = verify_color_confidence(frame, hsv, mask, (x, y, w, h))

            # Score this candidate
            score = score_candidate(contour, frame.shape, color_confidence, area)

            # Only keep if score is above threshold
            if score > 0:
                cx = x + w // 2
                cy = y + h // 2
                candidates.append({
                    'score': score,
                    'area': area,
                    'bbox': (x, y, w, h),
                    'center': (cx, cy),
                    'confidence': color_confidence,
                    'contour': contour
                })

    if not candidates:
        return False, 0, 0, 0, None, 0.0, []

    # Sort by score (highest first)
    candidates.sort(key=lambda c: c['score'], reverse=True)

    # Get best candidate
    best = candidates[0]
    cx, cy = best['center']

    # Return based on what's requested
    if return_all_candidates:
        return True, cx, cy, best['area'], best['bbox'], best['confidence'], candidates[1:4]
    else:
        return True, cx, cy, best['area'], best['bbox'], best['confidence'], []

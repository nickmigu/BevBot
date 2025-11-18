# -*- coding: utf-8 -*-
import cv2
import numpy as np
import json
from cup_detector import detect_red_cup

# IP Webcam stream URL
# STREAM_URL = "http://192.168.1.160:8080/video"
STREAM_URL = "http://192.168.1.85:8080/video"

# Config file path
CONFIG_FILE = "hsv_config.json"

# Processing scale for performance (same as tracker)
PROCESS_SCALE = 0.3

# Flip video upside down (useful if camera is mounted upside down)
FLIP_VIDEO = False  # Set to True to rotate video 180 degrees

class SimpleHSVCalibrator:
    def __init__(self):
        self.window_name = "Click Calibration - Click on the cup!"
        self.detection_window = "Detection Preview - Live Results"
        self.samples = []  # Store (h, s, v) tuples from clicks
        self.current_frame = None
        self.current_hsv = None
        self.current_config = None  # Store latest config for detection

        # Create windows and set mouse callback
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 600)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        # Create detection preview window
        cv2.namedWindow(self.detection_window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.detection_window, 800, 600)

        print("\n" + "="*60)
        print("INSTANT HSV CALIBRATION - Click to Sample")
        print("="*60)
        print("\nInstructions:")
        print("  1. Click on the red cup (auto-saves after each click)")
        print("  2. Watch the 'Detection Preview' window for live results!")
        print("  3. Click 5+ times on different spots for best results")
        print("  4. Press 'C' to clear samples and start over")
        print("  5. Press 'Q' to quit\n")
        print("TIP: Two windows will open:")
        print("  - Calibration window: Click on the cup here")
        print("  - Detection Preview: See what detect_red_cup() finds\n")

    def is_red_hue(self, h):
        """Check if hue value is in red range"""
        return h <= 30 or h >= 150

    def sample_region(self, x, y, size=5):
        """Sample a region around clicked point and return median HSV values"""
        height, width = self.current_hsv.shape[:2]

        # Calculate region boundaries
        half_size = size // 2
        y_start = max(0, y - half_size)
        y_end = min(height, y + half_size + 1)
        x_start = max(0, x - half_size)
        x_end = min(width, x + half_size + 1)

        # Extract region
        region = self.current_hsv[y_start:y_end, x_start:x_end]

        # Calculate median for each channel
        h_median = np.median(region[:, :, 0])
        s_median = np.median(region[:, :, 1])
        v_median = np.median(region[:, :, 2])

        return int(h_median), int(s_median), int(v_median)

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks to sample colors"""
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.current_frame is None or self.current_hsv is None:
                return

            # Sample 5x5 region around click (more robust than single pixel)
            h, s, v = self.sample_region(x, y, size=5)

            # Validate if this looks like red
            if not self.is_red_hue(h):
                print(f"⚠ Warning: H={h} is not red (should be 0-30 or 150-180)")
                print(f"  Click on the RED cup, not background. Adding anyway...")

            # Store sample
            self.samples.append((x, y, int(h), int(s), int(v)))

            print(f"Sample {len(self.samples)}: H={h}, S={s}, V={v}")

            # Auto-save after each click (cumulative range expansion)
            self.save_config()

    def remove_outliers(self, values):
        """Remove outliers using median absolute deviation (MAD) method"""
        if len(values) < 3:
            return values  # Need at least 3 samples for outlier detection

        values_array = np.array(values)
        median = np.median(values_array)
        mad = np.median(np.abs(values_array - median))

        # If MAD is 0, all values are the same, no outliers
        if mad == 0:
            return values

        # Modified z-score threshold (2.5 is standard for outlier detection)
        modified_z_scores = 0.6745 * (values_array - median) / mad
        threshold = 2.5

        # Keep only non-outliers
        filtered = [v for v, z in zip(values, np.abs(modified_z_scores)) if z < threshold]

        # If we filtered out too many, keep original
        if len(filtered) < max(2, len(values) * 0.5):
            return values

        return filtered

    def calculate_adaptive_tolerance(self, values, min_tol, max_tol, multiplier=2.5):
        """Calculate adaptive tolerance based on sample variance"""
        if len(values) < 2:
            return max_tol  # Use max tolerance for single sample

        std_dev = np.std(values)
        tolerance = int(max(min_tol, std_dev * multiplier))
        tolerance = min(tolerance, max_tol)  # Cap at maximum

        return tolerance

    def detect_hue_wraparound(self, h_values):
        """Detect if hue values span the red wraparound (0/180 boundary)"""
        # Red wraps around: 0-30 and 150-180
        has_low_red = any(h <= 30 for h in h_values)
        has_high_red = any(h >= 150 for h in h_values)

        return has_low_red and has_high_red

    def calculate_hue_range_with_wraparound(self, h_values):
        """Calculate hue range handling red color wraparound"""
        if not self.detect_hue_wraparound(h_values):
            # No wraparound, simple case
            return min(h_values), max(h_values)

        # Wraparound detected - split into low and high red values
        low_reds = [h for h in h_values if h <= 90]  # 0-90 considered "low"
        high_reds = [h for h in h_values if h > 90]  # 90-180 considered "high"

        # Use the group with more samples as primary
        if len(low_reds) >= len(high_reds):
            # Mostly low red values
            h_min = min(low_reds) if low_reds else 0
            h_max = max(low_reds) if low_reds else 30
        else:
            # Mostly high red values
            h_min = min(high_reds) if high_reds else 160
            h_max = max(high_reds) if high_reds else 180

        return h_min, h_max

    def calculate_hsv_ranges(self):
        """Calculate HSV ranges from collected samples with outlier rejection and adaptive tolerance"""
        if len(self.samples) == 0:
            print("WARNING: No samples collected! Click on the cup first.")
            return None

        # Extract HSV values
        h_values = [s[2] for s in self.samples]
        s_values = [s[3] for s in self.samples]
        v_values = [s[4] for s in self.samples]

        # Remove outliers (only if we have enough samples)
        if len(self.samples) >= 3:
            h_values = self.remove_outliers(h_values)
            s_values = self.remove_outliers(s_values)
            v_values = self.remove_outliers(v_values)

            outliers_removed = len(self.samples) - len(h_values)
            if outliers_removed > 0:
                print(f"  ℹ Removed {outliers_removed} outlier(s)")

        # Calculate adaptive tolerances
        h_tolerance = self.calculate_adaptive_tolerance(h_values, min_tol=8, max_tol=15, multiplier=2.5)
        s_tolerance = self.calculate_adaptive_tolerance(s_values, min_tol=25, max_tol=40, multiplier=2.0)
        v_tolerance = self.calculate_adaptive_tolerance(v_values, min_tol=25, max_tol=40, multiplier=2.0)

        print(f"  ℹ Adaptive tolerances: H=±{h_tolerance}, S=±{s_tolerance}, V=±{v_tolerance}")

        # Handle hue wraparound for red color
        h_min_base, h_max_base = self.calculate_hue_range_with_wraparound(h_values)

        # Apply tolerance
        h_min = max(0, h_min_base - h_tolerance)
        h_max = min(180, h_max_base + h_tolerance)
        s_min = max(0, min(s_values) - s_tolerance)
        s_max = min(255, max(s_values) + s_tolerance)
        v_min = max(0, min(v_values) - v_tolerance)
        v_max = min(255, max(v_values) + v_tolerance)

        # Check if we need dual ranges for red wraparound
        if self.detect_hue_wraparound(h_values):
            # Create two ranges to cover wraparound
            config = {
                "red_lower_1": [0, int(s_min), int(v_min)],
                "red_upper_1": [30, int(s_max), int(v_max)],
                "red_lower_2": [150, int(s_min), int(v_min)],
                "red_upper_2": [180, int(s_max), int(v_max)]
            }
            print(f"  ℹ Red wraparound detected - using dual ranges")
        else:
            # Single range
            config = {
                "red_lower_1": [int(h_min), int(s_min), int(v_min)],
                "red_upper_1": [int(h_max), int(s_max), int(v_max)],
                "red_lower_2": [160, 100, 100],  # Backup range
                "red_upper_2": [180, 255, 255]
            }

        return config

    def save_config(self):
        """Save HSV ranges to config file (auto-called after each click)"""
        config = self.calculate_hsv_ranges()

        if config is None:
            return

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        # Store config for live detection preview
        self.current_config = config

        # Concise feedback for auto-save
        print(f"  -> Auto-saved! Range: H={config['red_lower_1'][0]}-{config['red_upper_1'][0]}, "
              f"S={config['red_lower_1'][1]}-{config['red_upper_1'][1]}, "
              f"V={config['red_lower_1'][2]}-{config['red_upper_1'][2]}")

    def clear_samples(self):
        """Clear all collected samples"""
        self.samples = []
        self.current_config = None
        print("\nCleared all samples. Click on the cup again.\n")

    def draw_detection_preview(self, frame):
        """Draw live detection preview showing what detect_red_cup() sees"""
        preview = frame.copy()

        # Only run detection if we have a config
        if self.current_config is None:
            # Show message when no samples yet
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(preview, "No calibration yet - Click on the cup!", (10, 30),
                       font, 0.8, (0, 165, 255), 2)
            cv2.putText(preview, "Detection will appear here after first click", (10, 70),
                       font, 0.6, (200, 200, 200), 1)
            return preview

        # Run detection with current config (using improved detector)
        found, cx, cy, area, bbox, confidence, _ = detect_red_cup(frame, self.current_config)

        if found:
            # Draw bounding box
            if bbox:
                x, y, w, h = bbox
                # Color based on confidence: green = good, yellow = ok
                color = (0, 255, 0) if confidence >= 0.75 else (0, 255, 255)
                cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)
                cv2.circle(preview, (cx, cy), 5, (255, 0, 0), -1)

            # Draw detection info
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(preview, "CUP DETECTED!", (10, 30),
                       font, 0.8, (0, 255, 0), 2)
            cv2.putText(preview, f"Confidence: {confidence*100:.0f}%", (10, 70),
                       font, 0.6, (0, 255, 0), 2)
            cv2.putText(preview, f"Area: {int(area)} pixels", (10, 100),
                       font, 0.6, (0, 255, 0), 2)
            cv2.putText(preview, f"Center: ({cx}, {cy})", (10, 130),
                       font, 0.6, (0, 255, 0), 2)
        else:
            # No detection
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(preview, "No cup detected", (10, 30),
                       font, 0.8, (0, 0, 255), 2)
            cv2.putText(preview, "Click more areas of the cup to expand range", (10, 70),
                       font, 0.6, (200, 200, 200), 1)
            cv2.putText(preview, "OR: Chair detected instead? Calibrate tighter!", (10, 100),
                       font, 0.5, (0, 165, 255), 1)

        # Show sample count
        cv2.putText(preview, f"Samples: {len(self.samples)}", (10, preview.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return preview

    def draw_ui(self, frame):
        """Draw UI overlay on frame"""
        display = frame.copy()

        # Draw click markers
        for i, (x, y, h, s, v) in enumerate(self.samples):
            # Draw circle
            cv2.circle(display, (x, y), 15, (0, 255, 0), 2)
            cv2.circle(display, (x, y), 3, (0, 255, 0), -1)
            # Draw number
            cv2.putText(display, str(i+1), (x+20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw instructions overlay
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (display.shape[1], 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display, "Click on the cup - Auto-saves instantly!", (10, 30),
                   font, 0.8, (255, 255, 255), 2)
        cv2.putText(display, f"Samples: {len(self.samples)} | C: Clear | Q: Quit",
                   (10, 65), font, 0.6, (200, 200, 200), 1)

        # Show status
        if len(self.samples) >= 5:
            cv2.putText(display, f"{len(self.samples)} samples - Great! Add more or test with tracker", (10, 95),
                       font, 0.6, (0, 255, 0), 2)
        elif len(self.samples) > 0:
            cv2.putText(display, f"Click {5 - len(self.samples)} more times (recommended)", (10, 95),
                       font, 0.6, (0, 200, 255), 2)

        return display

    def run(self):
        """Main calibration loop"""
        cap = cv2.VideoCapture(STREAM_URL)

        if not cap.isOpened():
            print(f"ERROR: Could not open video stream: {STREAM_URL}")
            return

        print(f"Stream opened at {PROCESS_SCALE*100:.0f}% resolution for better performance\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to get frame")
                continue

            # Flip video if needed (camera mounted upside down)
            if FLIP_VIDEO:
                frame = cv2.flip(frame, -1)  # -1 flips both horizontally and vertically (180 degree rotation)

            # Downscale for performance (same as tracker)
            height, width = frame.shape[:2]
            process_width = int(width * PROCESS_SCALE)
            process_height = int(height * PROCESS_SCALE)
            process_frame = cv2.resize(frame, (process_width, process_height))

            # Store downscaled frame and HSV for sampling
            self.current_frame = process_frame
            self.current_hsv = cv2.cvtColor(process_frame, cv2.COLOR_BGR2HSV)

            # Draw UI for calibration window
            display = self.draw_ui(process_frame)

            # Draw detection preview
            detection_preview = self.draw_detection_preview(process_frame)

            # Show both windows
            cv2.imshow(self.window_name, display)
            cv2.imshow(self.detection_window, detection_preview)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == ord('Q'):
                print("\nExiting calibration...")
                break
            elif key == ord('s') or key == ord('S'):
                # Manual save (redundant now but kept for compatibility)
                print("\n(Config already auto-saves after each click)")
            elif key == ord('c') or key == ord('C'):
                self.clear_samples()

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

def main():
    calibrator = SimpleHSVCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Calibration tool for dash cam speed estimation.

Usage:
    python calibrate.py --profile config/family_car.yaml --image assets/calibrate.jpg

You need a still image of a flat road with at least 4 known points forming
a rectangle on the ground (e.g., parking bay lines, lane markings 2m apart).
Click the 4 corners in order: top-left, top-right, bottom-right, bottom-left.
The tool computes the IPM homography and updates the profile YAML.
"""

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

# Global state for mouse callback
clicked_points = []
image_display = None


def mouse_callback(event, x, y, flags, param):
    global clicked_points, image_display
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append((x, y))
            # Draw marker
            cv2.circle(image_display, (x, y), 8, (0, 0, 255), -1)
            cv2.putText(image_display, str(len(clicked_points)), (x + 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.imshow("Calibrate", image_display)
            if len(clicked_points) == 4:
                print("[INFO] All 4 points selected. Press any key to compute.")


def load_profile(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_profile(path: Path, profile: dict):
    with open(path, "w") as f:
        yaml.dump(profile, f, sort_keys=False, default_flow_style=False)
    print(f"[INFO] Updated profile saved to {path}")


def compute_ipm(image_path: Path, profile: dict, real_width_m: float, real_height_m: float):
    global clicked_points, image_display

    img = cv2.imread(str(image_path))
    if img is None:
        print(f"[ERROR] Cannot load image: {image_path}")
        sys.exit(1)

    h, w = img.shape[:2]
    image_display = img.copy()

    print("[INFO] Click 4 ground-plane corners in order:")
    print("       1 = top-left, 2 = top-right, 3 = bottom-right, 4 = bottom-left")
    print("       (from the camera's perspective)")

    cv2.namedWindow("Calibrate")
    cv2.setMouseCallback("Calibrate", mouse_callback)
    cv2.imshow("Calibrate", image_display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if len(clicked_points) != 4:
        print("[ERROR] Need exactly 4 points.")
        sys.exit(1)

    src_pts = np.array(clicked_points, dtype=np.float32)

    # Destination: bird's-eye rectangle with known real-world size
    ipm_w = profile["ipm"]["width"]
    ipm_h = profile["ipm"]["height"]

    # Map real dimensions to IPM output pixels
    # We fit the known rectangle into the IPM canvas, preserving aspect ratio
    scale_x = ipm_w / real_width_m
    scale_y = ipm_h / real_height_m
    scale = min(scale_x, scale_y)

    dst_w = real_width_m * scale
    dst_h = real_height_m * scale
    offset_x = (ipm_w - dst_w) / 2
    offset_y = (ipm_h - dst_h) / 2

    dst_pts = np.array([
        [offset_x, offset_y],
        [offset_x + dst_w, offset_y],
        [offset_x + dst_w, offset_y + dst_h],
        [offset_x, offset_y + dst_h],
    ], dtype=np.float32)

    H = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Compute meters_per_pixel from scale
    meters_per_pixel = 1.0 / scale

    # Update profile
    profile["ipm"]["homography"] = H.tolist()
    profile["ipm"]["meters_per_pixel"] = round(meters_per_pixel, 6)

    # Visual preview
    ipm_preview = cv2.warpPerspective(img, H, (ipm_w, ipm_h))
    cv2.imshow("IPM Preview", ipm_preview)
    print(f"[INFO] Computed meters_per_pixel: {meters_per_pixel:.6f}")
    print("[INFO] Close preview window to save profile.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return profile


def estimate_from_camera_geometry(profile: dict):
    """
    Fallback / approximate: estimate meters_per_pixel from camera_height and tilt.
    Assumes a pinhole model. This is rough but gives a starting point.
    """
    h = profile["camera_height"]
    theta = math.radians(profile["tilt_angle"])
    fov_h = math.radians(profile["fov_horizontal"])

    # Distance to the center of the ROI on ground
    d_center = h / math.tan(theta)

    # At that distance, the width spanned by FOV
    w_center = 2 * d_center * math.tan(fov_h / 2)

    # Rough pixels-per-meter at IPM resolution
    ipm_w = profile["ipm"]["width"]
    mpp = w_center / ipm_w

    print(f"[INFO] Geometry-based estimate: meters_per_pixel = {mpp:.6f}")
    print("[WARN] This is approximate. Run with --image for accurate calibration.")
    profile["ipm"]["meters_per_pixel"] = round(mpp, 6)
    return profile


def main():
    parser = argparse.ArgumentParser(description="Calibrate dash cam for speed estimation")
    parser.add_argument("--profile", required=True, help="Path to vehicle YAML profile")
    parser.add_argument("--image", help="Path to still image with known ground rectangle")
    parser.add_argument("--width", type=float, default=2.5, help="Real-world width of rectangle (meters)")
    parser.add_argument("--height", type=float, default=4.0, help="Real-world height of rectangle (meters)")
    parser.add_argument("--geometry", action="store_true", help="Use camera height/tilt to estimate scale")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    profile = load_profile(profile_path)

    if args.image:
        profile = compute_ipm(
            Path(args.image), profile,
            real_width_m=args.width,
            real_height_m=args.height
        )
    elif args.geometry:
        profile = estimate_from_camera_geometry(profile)
    else:
        print("[ERROR] Provide --image for full calibration, or --geometry for rough estimate.")
        sys.exit(1)

    save_profile(profile_path, profile)


if __name__ == "__main__":
    main()
